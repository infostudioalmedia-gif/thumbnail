"""
نظام الثمبنيل - Thumbnail System
يأخذ فيديو (مسار من الجهاز / رابط درايف / رابط مباشر / رفع) ويطلع:
  - ثمبنيل عرضي لليوتيوب 1280x720
  - ثمبنيل طولي ستوري 1080x1920
"""
import os, re, sys, json, uuid, shutil, subprocess, urllib.request, urllib.parse
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory

BASE = Path(__file__).parent
JOBS = BASE / "jobs"
JOBS.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE / "static"), static_url_path="")
CLOUD = os.environ.get("ROOYA_CLOUD") == "1"  # نسخة أونلاين: بدون مسارات محلية
app.config["MAX_CONTENT_LENGTH"] = (2 if CLOUD else 20) * 1024 ** 3  # حد الرفع

N_CANDIDATES = 24

FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


# ----------------------------------------------------------------- video I/O
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")


def duration_of(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise RuntimeError("تعذر قراءة الفيديو (الملف تالف أو ليس فيديو)")


VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")


def _is_direct_video(url):
    """هل الرابط ملف فيديو مباشر؟ (امتداد أو Content-Type)"""
    if urllib.parse.urlparse(url).path.lower().endswith(VIDEO_EXT):
        return True
    if "dl=1" in url or "download" in url.lower():
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.headers.get_content_type().startswith("video/")
        except Exception:
            return False
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.headers.get_content_type().startswith("video/")
    except Exception:
        return False


def _ytdlp(url, job_dir):
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("الرابط ليس ملف فيديو مباشر. ثبّت yt-dlp لتحميله: pip install yt-dlp")
    opts = {"outtmpl": str(job_dir / "source.%(ext)s"), "format": "best[height<=1080]/best",
            "quiet": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            y.download([url])
    except Exception as e:
        raise RuntimeError(f"تعذر تحميل الرابط: {str(e)[:160]}")
    got = [f for f in job_dir.glob("source.*")]
    if not got:
        raise RuntimeError("تعذر تحميل الفيديو من هذا الرابط")
    return got[0]


def fetch_source(src, job_dir):
    """يرجع مسار ملف فيديو محلي من أي نوع مصدر."""
    src = src.strip().strip('"').strip("'")
    if not src:
        raise RuntimeError("ادخل مسار أو رابط الفيديو")
    if re.match(r"^https?://", src, re.I):
        out = job_dir / "source.mp4"
        if "drive.google.com" in src or "docs.google.com" in src:
            import gdown
            m = re.search(r"/d/([\w-]{15,})", src) or re.search(r"[?&]id=([\w-]{15,})", src)
            if not m:
                raise RuntimeError("لم أستطع استخراج ID الملف من رابط الدرايف")
            res = gdown.download(id=m.group(1), output=str(out), quiet=True)
            if not res or not out.exists():
                raise RuntimeError("فشل تحميل ملف الدرايف. تأكد أن الرابط 'أي شخص لديه الرابط' (Anyone with the link)")
        else:
            url = src
            if "dropbox.com" in url:  # روابط دروبوكس: حمّل مباشرة
                url = re.sub(r"dl=0", "dl=1", url) if "dl=" in url else url + ("&" if "?" in url else "?") + "dl=1"
            if _is_direct_video(url):
                urllib.request.urlretrieve(url, out)
            else:  # يوتيوب / فيميو / فيسبوك / أي صفحة فيديو
                out = _ytdlp(url, job_dir)
        return out
    if src.lower().startswith("file:///"):
        src = urllib.parse.unquote(src[8:])
    if CLOUD:
        raise RuntimeError("المسارات المحلية غير متاحة في النسخة الأونلاين. استخدم رابط درايف/رابط خارجي أو ارفع الملف.")
    p = Path(src)
    if not p.exists():
        raise RuntimeError(f"الملف غير موجود: {src}")
    return p


def extract_candidates(video, job_dir):
    dur = duration_of(video)
    cdir = job_dir / "cands"
    cdir.mkdir(exist_ok=True)
    start, end = dur * 0.06, dur * 0.95
    times = [start + (end - start) * i / (N_CANDIDATES - 1) for i in range(N_CANDIDATES)]
    items = []
    for i, t in enumerate(times):
        out = cdir / f"{i:02d}.jpg"
        run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
             "-vf", "scale='min(1920,iw)':-2", "-q:v", "2", str(out)])
        if not out.exists():
            continue
        score, faces = score_frame(out)
        items.append({"i": i, "t": round(t, 2), "score": score, "faces": faces, "file": out.name})
    if not items:
        raise RuntimeError("لم أستطع استخراج أي لقطة من الفيديو")
    return items, dur


def detect_faces(gray):
    h, w = gray.shape
    scale = 640 / w if w > 640 else 1
    small = cv2.resize(gray, None, fx=scale, fy=scale) if scale != 1 else gray
    faces = FACE.detectMultiScale(small, 1.15, 5, minSize=(40, 40))
    return [(int(x / scale), int(y / scale), int(fw / scale), int(fh / scale)) for x, y, fw, fh in faces]


def score_frame(path):
    img = cv2.imread(str(path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharp = min(cv2.Laplacian(gray, cv2.CV_64F).var() / 300.0, 1.0)
    bright = gray.mean() / 255.0
    bright_score = 1.0 - min(abs(bright - 0.45) / 0.45, 1.0)
    contrast = min(gray.std() / 70.0, 1.0)
    faces = detect_faces(gray)
    face_score = 0.0
    if faces:
        fw = max(f[2] for f in faces)
        face_score = min(fw / (gray.shape[1] * 0.25), 1.0)
    score = sharp * 0.35 + bright_score * 0.2 + contrast * 0.15 + face_score * 0.3
    return round(float(score), 3), len(faces)


def face_center(img_path):
    """مركز الوجه الأكبر (نسبة 0..1) أو None."""
    gray = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2GRAY)
    faces = detect_faces(gray)
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    H, W = gray.shape
    return ((x + w / 2) / W, (y + h / 2) / H)


# ------------------------------------------------------------- compositions
import design as D
from design import Image, ImageDraw, ImageFilter, ImageEnhance


def save_jpg(img, path, limit=1_900_000):
    img = img.convert("RGB")
    for q in (95, 90, 85, 80, 72):
        img.save(path, "JPEG", quality=q, optimize=True, subsampling=0)
        if os.path.getsize(path) <= limit:
            break


def pick_extra(meta, jd, chosen_t, n=2):
    """لقطات إضافية متنوعة من الفيديو (بعيدة زمنياً عن اللقطة الأساسية وعن بعضها)."""
    gap = max(3.0, meta.get("dur", 60) * 0.08)
    chosen, taken = [], [chosen_t]
    for it in sorted(meta["items"], key=lambda x: -x["score"]):
        if all(abs(it["t"] - t) >= gap for t in taken):
            chosen.append(Image.open(jd / "cands" / it["file"]).convert("RGB"))
            taken.append(it["t"])
        if len(chosen) >= n:
            break
    return chosen


def make_landscape(frame_path, extras, title, subtitle, face, layout, kash, kws, style=0):
    W, H = 1280, 720
    src = Image.open(frame_path).convert("RGB")
    rtl = D.has_arabic(title) if title else True
    if layout == "design":
        base = D.brand_bg((W, H), src)
        card_cx = 370 if rtl else W - 370
        card = D.make_card(src, (640, 440), 30, 7, angle=-2 if rtl else 2, center=face or (0.5, 0.45))
        D.put(base, card, card_cx, 315)
        if kws:
            D.chip_row(base, kws, card_cx, 640, 34)
        out = base.convert("RGB")
        if title:
            box = (W - 590, 80, W - 45, 640) if rtl else (45, 80, 590, 640)
            D.draw_title(out, title, box, 175, "right" if rtl else "left", subtitle, "middle", kash, style)
        return out
    # layout == photo : لقطة بملء الإطار + تدرّج كحلي هوية رؤية
    if src.height > src.width:
        base = D.brand_bg((W, H), src)
        fg = D.make_card(src, (int(H * 0.8 * src.width / src.height), int(H * 0.8)), 24, 6)
        D.put(base, fg, W // 2, H // 2)
    else:
        base = D.boost(D.cover(src, (W, H), face or (0.5, 0.45))).convert("RGBA")
    text_side = "right" if rtl else "left"
    if face:
        text_side = "left" if face[0] > 0.55 else ("right" if face[0] < 0.45 else text_side)
    base.alpha_composite(D.gradient_overlay((W, H), 0.2, D.DEEP, 0.94, horizontal=("left" if text_side == "right" else "right")))
    base.alpha_composite(D.gradient_overlay((W, H), 0.7, D.DEEP, 0.6))
    d = ImageDraw.Draw(base)
    bx = W - 16 if text_side == "right" else 0
    d.rectangle((bx, 0, bx + 16, H), fill=(*D.TEAL, 255))
    if kws:
        side_x = W - 160 if text_side == "left" else 160
        D.chip_row(base, kws, side_x, 70, 34, vertical=True)
    out = base.convert("RGB")
    if title:
        box = (W - 740, 70, W - 55, H - 60) if text_side == "right" else (55, 70, 740, H - 60)
        D.draw_title(out, title, box, 185, "right" if text_side == "right" else "left", subtitle, "bottom", kash, style)
    return out


def make_story(frame_path, extras, title, subtitle, face, mode, kash, kws, style=0):
    W, H = 1080, 1920
    src = Image.open(frame_path).convert("RGB")
    if mode == "design":
        base = D.brand_bg((W, H), src)
        # عمود لقطات جانبي (ريل) + لقطة رئيسية
        top, hh, gap = 850, 700, 24
        fh = (hh - 2 * gap) // 3
        col_x = 70 + 100
        for i in range(3):
            fr = extras[i] if i < len(extras) else src
            D.put(base, D.make_card(fr, (190, fh - 12), 22, 5), col_x, top + i * (fh + gap) + fh // 2, blur=16, off=(0, 10))
        main = D.make_card(src, (690, hh - 12), 34, 8, center=face or (0.5, 0.5))
        D.put(base, main, 70 + 200 + 28 + main.width // 2, top + hh // 2)
        if kws:
            D.chip_row(base, kws, W // 2, 790, 38)
        out = base.convert("RGB")
        if title:
            D.draw_title(out, title, (60, 255, W - 60, 740), 200, "center", subtitle, "middle", kash, style)
        return out
    if mode == "auto":
        mode = "crop" if (face and src.height >= 900 and src.width > src.height) else "blur"
    if mode == "crop":
        base = D.boost(D.cover(src, (W, H), face or (0.5, 0.5))).convert("RGBA")
    else:
        base = D.brand_bg((W, H), src)
        fg = D.make_card(src, (W - 80, int((W - 80) * src.height / src.width)), 30, 7)
        D.put(base, fg, W // 2, int(H * 0.5))
    base.alpha_composite(D.gradient_overlay((W, H), 0.45, D.DEEP, 0.92))
    out = base.convert("RGB")
    if title:
        D.draw_title(out, title, (60, 1040, W - 60, H - 360), 190, "center", subtitle, "bottom", kash, style)
    return out


# ------------------------------------------------------------------- routes
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.route("/")
def index():
    return app.send_static_file("index.html")


def _cleanup_jobs(max_age_h=3):
    """امسح الشغل القديم عشان مساحة السيرفر ما تتملي."""
    import time
    now = time.time()
    for d in JOBS.iterdir():
        try:
            if d.is_dir() and now - d.stat().st_mtime > max_age_h * 3600:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


@app.route("/api/analyze", methods=["POST"])
def analyze():
    _cleanup_jobs()
    job = uuid.uuid4().hex[:10]
    jd = JOBS / job
    jd.mkdir()
    try:
        save_dir, stem = None, "video"
        if "file" in request.files and request.files["file"].filename:
            up = request.files["file"]
            video = jd / ("source" + Path(up.filename).suffix)
            up.save(video)
        else:
            raw = request.form.get("source", "")
            video = fetch_source(raw, jd)
            if not re.match(r"^\s*https?://", raw, re.I):  # مسار محلي: احفظ جنب الفيديو
                save_dir, stem = str(video.parent), video.stem
        items, dur = extract_candidates(video, jd)
        best = max(items, key=lambda x: x["score"])
        (jd / "meta.json").write_text(json.dumps({"video": str(video), "items": items, "dur": dur, "save_dir": save_dir, "stem": stem}), encoding="utf-8")
        return jsonify(ok=True, job=job, duration=dur, best=best["i"],
                       items=[{**it, "url": f"/jobs/{job}/cands/{it['file']}"} for it in items])
    except Exception as e:
        shutil.rmtree(jd, ignore_errors=True)
        return jsonify(ok=False, error=str(e)), 400


@app.route("/api/render", methods=["POST"])
def render():
    d = request.get_json()
    jd = JOBS / d["job"]
    meta = json.loads((jd / "meta.json").read_text(encoding="utf-8"))
    it = next(x for x in meta["items"] if x["i"] == int(d["frame"]))
    frame = jd / "cands" / it["file"]
    # لقطة بدقة أعلى للمخرجات النهائية
    hi = jd / "hi.jpg"
    run(["ffmpeg", "-y", "-ss", str(it["t"]), "-i", meta["video"], "-frames:v", "1", "-q:v", "1", str(hi)])
    if hi.exists():
        frame = hi
    title = (d.get("title") or "").strip()
    sub = (d.get("subtitle") or "").strip()
    kash = max(1, int(d.get("kashida", 2)))  # التمديد إلزامي دائماً
    sidx = D.pick_style(int(d.get("style", -1)))
    face = face_center(frame)
    extras = pick_extra(meta, jd, it["t"], 3)
    kws = D.keywords(title + " " + sub, d.get("keywords", "")) if d.get("chips", True) else []
    land = make_landscape(frame, extras, title, sub, face, d.get("land_layout", "photo"), kash, kws, sidx)
    story = make_story(frame, extras, title, sub, face, d.get("story_mode", "design"), kash, kws, sidx)
    tag = uuid.uuid4().hex[:5]
    lp, sp = jd / f"youtube_{tag}.jpg", jd / f"story_{tag}.jpg"
    save_jpg(land, lp)
    save_jpg(story, sp)
    out = BASE / "output"
    out.mkdir(exist_ok=True)
    shutil.copy(lp, out / f"{d['job']}_youtube_1280x720.jpg")
    shutil.copy(sp, out / f"{d['job']}_story_1080x1920.jpg")
    saved_to = None
    if meta.get("save_dir"):  # الفيديو من الجهاز: احفظ في نفس فولدره
        stem = meta.get("stem", "video")
        sd = Path(meta["save_dir"])
        shutil.copy(lp, sd / f"{stem}_youtube_1280x720.jpg")
        shutil.copy(sp, sd / f"{stem}_story_1080x1920.jpg")
        saved_to = str(sd)
    return jsonify(ok=True, landscape=f"/jobs/{d['job']}/{lp.name}", story=f"/jobs/{d['job']}/{sp.name}",
                   saved_to=saved_to, stem=meta.get("stem", "thumbnail"),
                   style=sidx, style_name=D.STYLES[sidx]["name"], styles=len(D.STYLES))


@app.route("/jobs/<path:p>")
def jobs_files(p):
    return send_from_directory(JOBS, p)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    if CLOUD:
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        import webbrowser, threading
        threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        app.run(host="127.0.0.1", port=port, debug=False)
