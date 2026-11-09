"""
محرك التصميم - هوية رؤية
خط جرافيك + تمديد + ستايل طبقات + خلفية براند + كروت لقطات + أيقونات من المحتوى
"""
import re, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import arabic_reshaper
from bidi.algorithm import get_display

BASE = Path(__file__).parent
FONT_TITLE = str(BASE / "fonts" / "ArbFONTS-TheYearofHandicrafts-Bold.otf")
FONT_SUB = FONT_TITLE  # نفس الخط في كل التصاميم
LOGO = BASE / "assets" / "logo_white.png"

# ---- ألوان هوية رؤية ----
NAVY_STOPS = [(0.0, (53, 97, 158)), (0.34, (36, 57, 125)), (0.66, (25, 39, 103)), (1.0, (18, 27, 82))]
TEAL = (79, 230, 213)
TEAL_LIGHT = (184, 255, 244)
TEAL_DARK = (12, 92, 98)
GOLD = (255, 210, 122)
CREAM = (255, 239, 194)
GOLD_DARK = (156, 107, 21)
GOLD_MID = (217, 162, 63)
DEEP = (9, 16, 56)


def tfont(size): return ImageFont.truetype(FONT_TITLE, size)
def sfont(size): return ImageFont.truetype(FONT_SUB, size)


# ------------------------------------------------------------ Arabic text
def has_arabic(s): return bool(re.search(r"[؀-ۿ]", s))
_CMAPS = {}


def _cmap(path):
    if path not in _CMAPS:
        from fontTools.ttLib import TTFont
        _CMAPS[path] = set(TTFont(path).getBestCmap().keys())
    return _CMAPS[path]


def _fallback(s, path):
    """الخط يعتمد على GSUB للأشكال المنفصلة؛ نرجّع أي شكل ناقص لحرفه الأصلي."""
    import unicodedata
    cm = _cmap(path)
    out = []
    for ch in s:
        if ord(ch) in cm or ord(ch) < 0x80 or ch == " ":
            out.append(ch)
            continue
        dec = unicodedata.decomposition(ch).split()
        base = "".join(chr(int(x, 16)) for x in dec if not x.startswith("<"))
        out.append(base[::-1] if base and all(ord(c) in cm for c in base) else ch)
    return "".join(out)


_RESHAPER = arabic_reshaper.ArabicReshaper(configuration={"support_ligatures": False})


def shape(s, path=None):
    return _fallback(get_display(_RESHAPER.reshape(s)), path or FONT_TITLE)

JOIN_NEXT = set("بتثجحخسشصضطظعغفقكلمنهيئ")
AR_LETTERS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويىأإآؤئة")


def kashida(text, level):
    """تمديد: level 0 بدون / 1 خفيف (أطول كلمة) / 2 متوسط / 3 قوي"""
    if level <= 0 or not has_arabic(text):
        return text
    words = text.split(" ")
    ar_idx = [i for i, w in enumerate(words) if has_arabic(w)]
    if not ar_idx:
        return text
    if level == 1:
        targets = {max(ar_idx, key=lambda i: len(words[i]))}
        n_tat = 3
    elif level == 2:
        targets = {i for i in ar_idx if len(words[i]) >= 4} or set(ar_idx)
        n_tat = 2
    else:
        targets = {i for i in ar_idx if len(words[i]) >= 3} or set(ar_idx)
        n_tat = 3
    for i in targets:
        w = words[i]
        cands = []
        for p in range(len(w) - 1):
            a, b = w[p], w[p + 1]
            if a in JOIN_NEXT and b in AR_LETTERS and b != "ء":
                if a == "ل" and b in "اأإآ":
                    continue
                cands.append(p)
        if not cands:
            continue
        # أفضل موضع: قرب أول ثلث الكلمة (شكل التمديد التقليدي)
        target = max(1, len(w) * 0.35)
        p = min(cands, key=lambda c: abs(c - target))
        positions = [p]
        if level == 3 and len(cands) > 1:
            q = max(cands, key=lambda c: abs(c - p))
            if abs(q - p) >= 2:
                positions.append(q)
        for p in sorted(positions, reverse=True):
            w = w[:p + 1] + "ـ" * n_tat + w[p + 1:]
        words[i] = w
    if not any("ـ" in w for w in words):  # التمديد إلزامي: لو ما اتمدّد شيء، مدّد أي كلمة تقبل
        for i in sorted(ar_idx, key=lambda k: -len(words[k])):
            w = words[i]
            cands = [p for p in range(len(w) - 1)
                     if w[p] in JOIN_NEXT and w[p + 1] in AR_LETTERS and not (w[p] == "ل" and w[p + 1] in "اأإآ")]
            if cands:
                p = cands[0]
                words[i] = w[:p + 1] + "ـ" * 3 + w[p + 1:]
                break
    return " ".join(words)


def text_w(draw, s, f, stroke=0):
    b = draw.textbbox((0, 0), shape(s, f.path), font=f, stroke_width=stroke)
    return b[2] - b[0]


def wrap(draw, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if text_w(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, max_w, max_h, max_size, min_size=50, max_lines=3):
    size = max_size
    while size >= min_size:
        f = tfont(size)
        lines = wrap(draw, text, f, max_w)
        lh = int(size * 1.12)
        if len(lines) <= max_lines and len(lines) * lh <= max_h:
            return f, lines, lh
        size -= 4
    f = tfont(min_size)
    return f, wrap(draw, text, f, max_w)[:max_lines], int(min_size * 1.12)


# ----------------------------------------------------------- title style
def _lerp(c0, c1, t):
    return tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def _shift(mask, dx, dy):
    out = Image.new("L", mask.size, 0)
    out.paste(mask, (dx, dy))
    return out


def _vgrad(size, y0, y1, c0, c1):
    W, H = size
    r = np.clip((np.arange(H) - y0) / max(1, (y1 - y0)), 0, 1)[:, None]
    col = np.array(c0)[None, :] * (1 - r) + np.array(c1)[None, :] * r
    arr = np.broadcast_to(col[:, None, :], (H, W, 3)).astype(np.uint8)
    return Image.fromarray(arr, "RGB")

# ---------------------------------------------------------------- ستايلات الطبقات
# كلها من ألوان هوية رؤية: كحلي / أزرق / تركواز-منت / أبيض. يتغيّر ستايل مختلف مع كل Generate.
BLUE = (31, 81, 148)
MINT_TINT = (221, 255, 250)
STYLES = [
    dict(name="منت ثلاثي الأبعاد", face=((255, 255, 255), (214, 255, 249)), ext=(TEAL_DARK, TEAL),
         kface=(TEAL_LIGHT, TEAL), kext=((36, 57, 125), (53, 97, 158)), outline=DEEP, outline2=None,
         glow=TEAL, glow_a=0.55, dx=-0.35, depth=1.0),
    dict(name="ستيكر أبيض", face=(TEAL_LIGHT, TEAL), ext=((15, 25, 79), (36, 57, 125)),
         kface=((255, 255, 255), MINT_TINT), kext=((15, 25, 79), BLUE), outline=(255, 255, 255), outline2=DEEP,
         glow=BLUE, glow_a=0.5, dx=-0.3, depth=0.9),
    dict(name="كتلة زرقاء", face=((255, 255, 255), (214, 232, 250)), ext=((24, 44, 110), BLUE),
         kface=(TEAL_LIGHT, TEAL), kext=((10, 20, 70), (36, 57, 125)), outline=DEEP, outline2=None,
         glow=TEAL, glow_a=0.4, dx=0.35, depth=1.15),
    dict(name="حلقة منت", face=(TEAL_LIGHT, (120, 245, 230)), ext=(TEAL_DARK, (30, 150, 150)),
         kface=((255, 255, 255), MINT_TINT), kext=((24, 44, 110), BLUE), outline=DEEP, outline2=TEAL,
         glow=TEAL, glow_a=0.7, dx=-0.35, depth=0.95),
    dict(name="مسطّح جريء", face=((255, 255, 255), (255, 255, 255)), ext=(DEEP, DEEP),
         kface=(TEAL, TEAL), kext=(DEEP, DEEP), outline=DEEP, outline2=TEAL,
         glow=BLUE, glow_a=0.35, dx=0.0, depth=0.45),
    dict(name="ظل يمين", face=(TEAL, (255, 255, 255)), ext=((36, 57, 125), BLUE),
         kface=((255, 255, 255), TEAL_LIGHT), kext=(TEAL_DARK, (40, 170, 165)), outline=DEEP, outline2=None,
         glow=TEAL, glow_a=0.45, dx=0.6, depth=1.0),
    dict(name="كحلي بحد منت", face=((53, 97, 158), (15, 25, 79)), ext=(TEAL_DARK, TEAL),
         kface=(TEAL_LIGHT, TEAL), kext=((15, 25, 79), (36, 57, 125)), outline=TEAL, outline2=DEEP,
         glow=TEAL, glow_a=0.6, dx=-0.3, depth=0.9),
    dict(name="تدرّج منت وأزرق", face=((255, 255, 255), TEAL), ext=(DEEP, (36, 57, 125)),
         kface=(TEAL, (95, 168, 220)), kext=(DEEP, BLUE), outline=(255, 255, 255), outline2=DEEP,
         glow=TEAL, glow_a=0.5, dx=-0.35, depth=1.0),
]
_LAST_STYLE = [-1]


def pick_style(idx=-1):
    """idx < 0: عشوائي مختلف عن آخر ستايل؛ غير كده: ستايل محدد."""
    import random as _r
    if idx is not None and 0 <= idx < len(STYLES):
        _LAST_STYLE[0] = idx
        return idx
    choices = [i for i in range(len(STYLES)) if i != _LAST_STYLE[0]]
    idx = _r.choice(choices)
    _LAST_STYLE[0] = idx
    return idx


def draw_title(img, text, box, max_size, align="center", subtitle="", anchor="middle", kash=0, style=0):
    """عنوان بخط جرافيك + تمديد + ستايل طبقات (وهج، ظل، حد كحلي، سُمك 3D، وجه متدرّج، لمعة)."""
    text = kashida(text, kash)
    W, H = img.size
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    sub_h = 0
    sf = None
    if subtitle:
        sf = sfont(max(32, int(max_size * 0.27)))
        sub_h = int(sf.size * 1.55) + 40
    f, lines, lh = fit_text(d, text, x1 - x0, (y1 - y0) - sub_h, max_size)
    total = len(lines) * lh
    block = total + sub_h
    if anchor == "top":
        y = y0
    elif anchor == "bottom":
        y = y1 - block
    else:
        y = y0 + ((y1 - y0) - block) / 2
    y = int(y)
    st = STYLES[style % len(STYLES)] if isinstance(style, int) else style
    stroke = max(6, f.size // 10)
    depth = max(8, int(f.size // 8 * st["depth"]))
    dx = st["dx"]

    pos = []
    yy = y
    for line in lines:
        w = text_w(d, line, f)
        if align == "right":
            x = x1 - w
        elif align == "left":
            x = x0
        else:
            x = x0 + (x1 - x0 - w) / 2
        pos.append((int(x), yy))
        yy += lh

    # كل الأسطر: وهج + ظل
    glow = Image.new("L", (W, H), 0)
    shadow = Image.new("L", (W, H), 0)
    masks = []
    for line, (x, yl) in zip(lines, pos):
        s = shape(line, f.path)
        mf = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mf).text((x, yl), s, font=f, fill=255)
        mo = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mo).text((x, yl), s, font=f, fill=255, stroke_width=stroke)
        mo2 = None
        if st.get("outline2"):
            mo2 = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mo2).text((x, yl), s, font=f, fill=255, stroke_width=stroke + max(6, stroke * 3 // 4))
        masks.append((mf, mo, mo2))
        glow = ImageChops.lighter(glow, mo2 or mo)
        shadow = ImageChops.lighter(shadow, _shift(mo2 or mo, -4, depth + 16))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = glow.filter(ImageFilter.GaussianBlur(f.size // 4)).point(lambda v: int(v * st["glow_a"]))
    layer.paste((*st["glow"], 255), (0, 0), g)
    sh = shadow.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.65))
    layer.paste((0, 0, 0, 255), (0, 0), sh)

    for i, (mf, mo, mo2) in enumerate(masks):
        key = (i == len(masks) - 1 and len(masks) > 1)  # آخر سطر = لون ثانٍ
        # الحد (مزدوج لو الستايل فيه outline2)
        if mo2 is not None:
            for k in range(depth + 1):
                layer.paste((*st["outline2"], 255), (0, 0), _shift(mo2, int(k * dx), k))
        for k in range(depth + 1):
            layer.paste((*st["outline"], 255), (0, 0), _shift(mo, int(k * dx), k))
        # سُمك 3D
        far, near = st["kext"] if key else st["ext"]
        for k in range(depth, 0, -1):
            t = (depth - k) / max(1, depth - 1)
            layer.paste((*_lerp(far, near, t), 255), (0, 0), _shift(mf, int(k * dx), k))
        # الوجه
        yl = pos[i][1]
        c0, c1 = st["kface"] if key else st["face"]
        grad = _vgrad((W, H), yl + lh * 0.15, yl + lh * 0.95, c0, c1)
        layer.paste(grad, (0, 0), mf)
        # لمعة علوية
        hi = ImageChops.subtract(mf, _shift(mf, 0, max(3, f.size // 22))).point(lambda v: int(v * 0.5))
        layer.paste((255, 255, 255, 255), (0, 0), hi)

    base = img.convert("RGBA")
    base.alpha_composite(layer)
    img.paste(base.convert("RGB"))

    if subtitle and sf:
        d = ImageDraw.Draw(img)
        s = shape(subtitle, sf.path)
        w = text_w(d, subtitle, sf)
        pad = 26
        bw, bh = w + pad * 2, int(sf.size * 1.55)
        by = y + total + depth + 18
        if align == "right":
            bx = x1 - bw
        elif align == "left":
            bx = x0
        else:
            bx = x0 + (x1 - x0 - bw) / 2
        d.rounded_rectangle((bx, by + 6, bx + bw, by + bh + 6), radius=bh // 2, fill=DEEP)
        d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=bh // 2, fill=TEAL)
        bb = d.textbbox((0, 0), s, font=sf)
        d.text((bx + (bw - (bb[2] - bb[0])) / 2 - bb[0], by + (bh - (bb[3] - bb[1])) / 2 - bb[1]),
               s, font=sf, fill=DEEP)


# --------------------------------------------------------- photo helpers
def cover(img, size, center=(0.5, 0.5)):
    tw, th = size
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    nw, nh = int(iw * s + 0.5), int(ih * s + 0.5)
    r = img.resize((nw, nh), Image.LANCZOS)
    cx, cy = center[0] * nw, center[1] * nh
    left = min(max(cx - tw / 2, 0), nw - tw)
    top = min(max(cy - th / 2, 0), nh - th)
    return r.crop((int(left), int(top), int(left) + tw, int(top) + th))


def boost(img):
    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Color(img).enhance(1.15)
    return ImageEnhance.Sharpness(img).enhance(1.2)


# --------------------------------------------------------- brand background
def brand_bg(size, frame=None, seed=3):
    W, H = size
    yy, xx = np.mgrid[0:H, 0:W]
    t = (xx / W) * 0.30 + (yy / H) * 0.70
    xs = [s[0] for s in NAVY_STOPS]
    arr = np.stack([np.interp(t, xs, [s[1][c] for s in NAVY_STOPS]) for c in range(3)], axis=-1).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    if frame is not None:  # صورة الفيديو مموهة جداً داخل الخلفية = ربط بالمحتوى
        tint = cover(frame, size).filter(ImageFilter.GaussianBlur(26))
        tint = ImageEnhance.Color(tint).enhance(0.4)
        img = Image.blend(img, tint, 0.16)
    img = img.convert("RGBA")
    rnd = random.Random(seed)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    step = int(min(W, H) / 11)
    for x in range(0, W, step):
        d.line((x, 0, x, H), fill=(*TEAL, 22), width=2)
    for y in range(0, H, step):
        d.line((0, y, W, y), fill=(*TEAL, 22), width=2)
    # دوائر على نمط اللوجو (نقطتين فوق بعض + حلقات)
    for _ in range(int(W * H / 160000)):
        r = rnd.randint(int(step * 0.25), int(step * 1.1))
        cx, cy = rnd.randint(0, W), rnd.randint(0, H)
        if rnd.random() < 0.5:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*TEAL, 48), width=4)
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*TEAL, 26))
            d.ellipse((cx - r, cy + r * 2 - r, cx + r, cy + r * 2 + r), fill=(*TEAL, 26))
    for _ in range(4):
        r = rnd.randint(7, 14)
        cx, cy = rnd.randint(0, W), rnd.randint(0, H)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*GOLD, 150))
    ov = ov.filter(ImageFilter.GaussianBlur(0.6))
    img.alpha_composite(ov)
    # وهج تركواز
    gl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(gl).ellipse((-W * 0.2, -H * 0.12, W * 0.62, H * 0.38), fill=255)
    gl = gl.filter(ImageFilter.GaussianBlur(min(W, H) * 0.14)).point(lambda v: int(v * 0.30))
    img.paste((*TEAL, 255), (0, 0), gl)
    return img


# ------------------------------------------------------------------ cards
def make_card(src, size, radius=28, bw=6, border=TEAL, angle=0, center=(0.5, 0.5)):
    w, h = size
    ss = 2
    c = cover(src, (w, h), center).convert("RGBA")
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius * ss, fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    W2, H2 = w + 2 * bw, h + 2 * bw
    bm = Image.new("L", (W2 * ss, H2 * ss), 0)
    ImageDraw.Draw(bm).rounded_rectangle((0, 0, W2 * ss - 1, H2 * ss - 1), (radius + bw) * ss, fill=255)
    bm = bm.resize((W2, H2), Image.LANCZOS)
    card = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    card.paste(Image.new("RGBA", (W2, H2), (*border, 255)), (0, 0), bm)
    card.paste(c, (bw, bw), m)
    if angle:
        card = card.rotate(angle, expand=True, resample=Image.BICUBIC)
    return card


def put(base, card, cx, cy, shadow=True, blur=26, off=(0, 20), alpha=150):
    x, y = int(cx - card.width / 2), int(cy - card.height / 2)
    if shadow:
        a = card.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha / 255))
        base.paste((3, 8, 30, 255), (x + off[0], y + off[1]), a)
    base.paste(card, (x, y), card)


# ------------------------------------------------------------------ icons
ICON_KEYWORDS = [
    ("bottle", r"لبن|حليب|ألبان|البان|لبنية|milk|dairy|زبادي|يوغرت|رايب|كريمة|قشطة|زبدة"),
    ("cheese", r"جبن|جبنة|فيتا|موزاريلا|رومي|شيدر|cheese|قريش|مخيض"),
    ("factory", r"مصنع|مصانع|إنتاج|انتاج|تصنيع|factory|مشروع|خط انتاج|خط إنتاج"),
    ("gear", r"ماكينة|ماكينات|معدات|آلة|الة|تشغيل|صيانة|machine|هندسة|تكنولوجيا"),
    ("flask", r"تحليل|معمل|مختبر|فحص|اختبار|lab|test|كيمياء|ميكروب|بكتيريا"),
    ("thermo", r"حرارة|بسترة|تعقيم|تبريد|تسخين|درجة|pasteur"),
    ("chart", r"ربح|أرباح|ارباح|تكلفة|تكاليف|مبيعات|نجاح|نمو|سوق|تسويق|استثمار|فلوس|مال"),
    ("shield", r"جودة|سلامة|معايير|شهادة|ايزو|iso|haccp|أمان|امان|ترخيص"),
]


def pick_icons(text, n=3):
    chosen = []
    for name, pat in ICON_KEYWORDS:
        if re.search(pat, text, re.I) and name not in chosen:
            chosen.append(name)
    for name in ("bottle", "factory", "cheese", "flask", "chart"):
        if len(chosen) >= n:
            break
        if name not in chosen:
            chosen.append(name)
    return chosen[:n]


def icon_img(name, color, S=400):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = S / 100.0
    P = lambda pts: [(x * u, y * u) for x, y in pts]
    fill = (*color, 255)
    cut = (0, 0, 0, 0)
    if name == "bottle":
        d.rounded_rectangle((38 * u, 6 * u, 62 * u, 22 * u), 4 * u, fill=fill)
        d.polygon(P([(40, 22), (60, 22), (74, 40), (74, 88), (26, 88), (26, 40)]), fill=fill)
        d.rounded_rectangle((26 * u, 78 * u, 74 * u, 94 * u), 7 * u, fill=fill)
        d.rounded_rectangle((34 * u, 46 * u, 66 * u, 72 * u), 6 * u, fill=cut)
        d.ellipse((43 * u, 52 * u, 57 * u, 66 * u), fill=fill)
        d.polygon(P([(50, 48), (56, 58), (44, 58)]), fill=fill)
    elif name == "cheese":
        d.polygon(P([(6, 76), (94, 76), (94, 44), (12, 22)]), fill=fill)
        d.rectangle((6 * u, 74 * u, 94 * u, 84 * u), fill=fill)
        for cx, cy, r in ((60, 60, 7), (36, 62, 5), (80, 54, 4), (26, 48, 3.5)):
            d.ellipse(((cx - r) * u, (cy - r) * u, (cx + r) * u, (cy + r) * u), fill=cut)
    elif name == "factory":
        d.polygon(P([(8, 90), (8, 30), (32, 46), (32, 30), (56, 46), (56, 30), (78, 46), (78, 10), (92, 10), (92, 90)]), fill=fill)
        for x in (18, 38, 58, 74):
            d.rectangle((x * u, 62 * u, (x + 9) * u, 74 * u), fill=cut)
    elif name == "gear":
        import math
        cx = cy = 50
        d.ellipse((24 * u, 24 * u, 76 * u, 76 * u), fill=fill)
        for i in range(8):
            a = math.radians(i * 45)
            ca, sa = math.cos(a), math.sin(a)
            pts = []
            for (rx, ry) in ((-7, 20), (7, 20), (7, 40), (-7, 40)):
                pts.append((cx + rx * ca - ry * sa, cy + rx * sa + ry * ca))
            d.polygon(P(pts), fill=fill)
        d.ellipse((38 * u, 38 * u, 62 * u, 62 * u), fill=cut)
    elif name == "flask":
        d.rectangle((38 * u, 8 * u, 62 * u, 42 * u), fill=fill)
        d.polygon(P([(38, 40), (62, 40), (92, 90), (8, 90)]), fill=fill)
        d.rounded_rectangle((32 * u, 4 * u, 68 * u, 14 * u), 4 * u, fill=fill)
        for cx, cy, r in ((50, 72, 5), (38, 80, 3.5), (62, 78, 4)):
            d.ellipse(((cx - r) * u, (cy - r) * u, (cx + r) * u, (cy + r) * u), fill=cut)
        d.rectangle((38 * u, 52 * u, 62 * u, 58 * u), fill=cut)
    elif name == "thermo":
        d.rounded_rectangle((40 * u, 6 * u, 60 * u, 66 * u), 10 * u, fill=fill)
        d.ellipse((28 * u, 50 * u, 72 * u, 94 * u), fill=fill)
        d.rounded_rectangle((46 * u, 20 * u, 54 * u, 70 * u), 4 * u, fill=cut)
        d.ellipse((40 * u, 62 * u, 60 * u, 82 * u), fill=cut)
        for y in (18, 30, 42):
            d.rectangle((66 * u, y * u, 80 * u, (y + 4) * u), fill=fill)
    elif name == "chart":
        d.rounded_rectangle((10 * u, 58 * u, 30 * u, 92 * u), 4 * u, fill=fill)
        d.rounded_rectangle((40 * u, 36 * u, 60 * u, 92 * u), 4 * u, fill=fill)
        d.rounded_rectangle((70 * u, 12 * u, 90 * u, 92 * u), 4 * u, fill=fill)
    else:  # shield
        d.polygon(P([(50, 5), (90, 20), (90, 52), (50, 95), (10, 52), (10, 20)]), fill=fill)
        d.line(P([(30, 48), (45, 63), (72, 32)]), fill=cut, width=int(9 * u), joint="curve")
    return im


def badge(name, D=140, style="navy"):
    ss = 2
    S = D * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if style == "gold":
        d.ellipse((0, 0, S - 1, S - 1), fill=(*GOLD, 255))
        d.ellipse((S * 0.05, S * 0.05, S * 0.95, S * 0.95), outline=(*DEEP, 255), width=max(3, ss * 3))
        col = DEEP
    else:
        d.ellipse((0, 0, S - 1, S - 1), fill=(*TEAL, 255))
        d.ellipse((S * 0.045, S * 0.045, S * 0.955, S * 0.955), fill=(*DEEP, 255))
        d.ellipse((S * 0.085, S * 0.085, S * 0.915, S * 0.915), outline=(*TEAL, 110), width=max(2, ss * 2))
        col = TEAL
    ic = icon_img(name, col).resize((int(S * 0.52), int(S * 0.52)), Image.LANCZOS)
    im.alpha_composite(ic, ((S - ic.width) // 2, (S - ic.height) // 2))
    return im.resize((D, D), Image.LANCZOS)


def add_logo(base, height, xy, anchor="tl"):
    if not LOGO.exists():
        return
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.resize((int(lg.width * height / lg.height), height), Image.LANCZOS)
    x, y = xy
    if anchor == "tr":
        x -= lg.width
    base.alpha_composite(lg, (int(x), int(y)))


def gradient_overlay(size, start_frac, color=DEEP, max_alpha=0.9, horizontal=None):
    """horizontal: 'left' | 'right' = اتجاه الكثافة؛ None = من الأسفل."""
    w, h = size
    if horizontal:
        ramp = np.linspace(0, 1, w) ** 1.2
        if horizontal == "left":
            ramp = ramp[::-1]
        arr = np.tile(ramp[None, :], (h, 1))
        # ابدأ التدرج من start_frac
        arr = np.clip((arr - start_frac) / (1 - start_frac), 0, 1)
    else:
        arr = np.zeros((h, w), dtype=np.float32)
        y0 = int(h * start_frac)
        arr[y0:, :] = (np.linspace(0, 1, h - y0) ** 1.3)[:, None]
    layer = Image.new("RGBA", size, (*color, 255))
    layer.putalpha(Image.fromarray((arr * max_alpha * 255).astype(np.uint8)))
    return layer


# ------------------------------------------------------- keyword chips
TOPIC_LABELS = {"bottle": "ألبان", "cheese": "أجبان", "factory": "تصنيع", "gear": "معدات",
                "flask": "تحليل", "thermo": "بسترة", "chart": "نمو", "shield": "جودة"}


def keywords(text, custom=""):
    if custom and custom.strip():
        return [k.strip() for k in re.split(r"[,،\n]", custom) if k.strip()][:4]
    labels = [TOPIC_LABELS[n] for n, pat in ICON_KEYWORDS if re.search(pat, text, re.I)]
    for dflt in ("ألبان", "تصنيع", "جودة"):
        if len(labels) >= 3:
            break
        if dflt not in labels:
            labels.append(dflt)
    return labels[:3]


def _chip(label, size):
    f = sfont(size)
    tmp = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    s = shape(label, f.path)
    bb = tmp.textbbox((0, 0), s, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    h = int(size * 1.95)
    dot = int(size * 0.5)
    w = tw + int(size * 1.7) + dot
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius=h * ss // 2, fill=(*DEEP, 235), outline=(*TEAL, 255), width=4 * ss // 2 * 1)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    # نقطة تركواز على اليمين (نمط نقاط اللوجو)
    cx = w - int(size * 0.75)
    d.ellipse((cx - dot // 2, h // 2 - dot // 2, cx + dot // 2, h // 2 + dot // 2), fill=(*TEAL, 255))
    d.text((int(size * 0.7) - bb[0], (h - th) / 2 - bb[1]), s, font=f, fill=(255, 255, 255))
    return im


def chip_row(base, labels, cx, cy, size=40, gap=18, vertical=False):
    chips = [_chip(l, size) for l in labels]
    if vertical:
        y = cy
        for c in chips:
            put(base, c, cx, y + c.height // 2, blur=10, off=(0, 8), alpha=120)
            y += c.height + gap
        return
    total = sum(c.width for c in chips) + gap * (len(chips) - 1)
    x = cx + total / 2  # RTL: الأول على اليمين
    for c in chips:
        put(base, c, x - c.width / 2, cy, blur=10, off=(0, 8), alpha=120)
        x -= c.width + gap
