/* استوديو الثمبنيل — نسخة المتصفح (GitHub Pages): كل المعالجة على جهاز المستخدم */
const $ = id => document.getElementById(id);
const NAVY = '#0F194F', BLUE = '#1F5194', TEAL = '#4FE6D5', TEAL_L = '#B8FFF4', TEAL_D = '#0C5C62', MINT_T = '#DDFFFA';
const FONT = 'Handicrafts';

/* ---------------- ستايلات الطبقات (ألوان رؤية) ---------------- */
const STYLES = [
  { name: 'منت ثلاثي الأبعاد', face: ['#FFFFFF', '#D6FFF9'], ext: [TEAL_D, TEAL], kface: [TEAL_L, TEAL], kext: ['#24397D', '#35619E'], outline: NAVY, outline2: null, glow: TEAL, glowA: .55, dx: -.35, depth: 1.0 },
  { name: 'ستيكر أبيض', face: [TEAL_L, TEAL], ext: [NAVY, '#24397D'], kface: ['#FFFFFF', MINT_T], kext: [NAVY, BLUE], outline: '#FFFFFF', outline2: NAVY, glow: BLUE, glowA: .5, dx: -.3, depth: .9 },
  { name: 'كتلة زرقاء', face: ['#FFFFFF', '#D6E8FA'], ext: ['#182C6E', BLUE], kface: [TEAL_L, TEAL], kext: ['#0A1446', '#24397D'], outline: NAVY, outline2: null, glow: TEAL, glowA: .4, dx: .35, depth: 1.15 },
  { name: 'حلقة منت', face: [TEAL_L, '#78F5E6'], ext: [TEAL_D, '#1E9696'], kface: ['#FFFFFF', MINT_T], kext: ['#182C6E', BLUE], outline: NAVY, outline2: TEAL, glow: TEAL, glowA: .7, dx: -.35, depth: .95 },
  { name: 'مسطّح جريء', face: ['#FFFFFF', '#FFFFFF'], ext: [NAVY, NAVY], kface: [TEAL, TEAL], kext: [NAVY, NAVY], outline: NAVY, outline2: TEAL, glow: BLUE, glowA: .35, dx: 0, depth: .45 },
  { name: 'ظل يمين', face: [TEAL, '#FFFFFF'], ext: ['#24397D', BLUE], kface: ['#FFFFFF', TEAL_L], kext: [TEAL_D, '#28AAA5'], outline: NAVY, outline2: null, glow: TEAL, glowA: .45, dx: .6, depth: 1.0 },
  { name: 'كحلي بحد منت', face: ['#35619E', NAVY], ext: [TEAL_D, TEAL], kface: [TEAL_L, TEAL], kext: [NAVY, '#24397D'], outline: TEAL, outline2: NAVY, glow: TEAL, glowA: .6, dx: -.3, depth: .9 },
  { name: 'تدرّج منت وأزرق', face: ['#FFFFFF', TEAL], ext: [NAVY, '#24397D'], kface: [TEAL, '#5FA8DC'], kext: [NAVY, BLUE], outline: '#FFFFFF', outline2: NAVY, glow: TEAL, glowA: .5, dx: -.35, depth: 1.0 },
];
let lastStyle = -1;
function pickStyle(i) {
  if (i >= 0 && i < STYLES.length) { lastStyle = i; return i; }
  const c = STYLES.map((_, k) => k).filter(k => k !== lastStyle);
  lastStyle = c[Math.floor(Math.random() * c.length)];
  return lastStyle;
}
STYLES.forEach((s, i) => { const o = document.createElement('option'); o.value = i; o.textContent = s.name; $('style').appendChild(o); });

/* ---------------- التمديد (كشيدة) ---------------- */
const JOIN_NEXT = new Set('بتثجحخسشصضطظعغفقكلمنهيئ');
const AR_LETTERS = new Set('ابتثجحخدذرزسشصضطظعغفقكلمنهويىأإآؤئة');
const hasAr = s => /[؀-ۿ]/.test(s);
function candPositions(w) {
  const c = [];
  for (let p = 0; p < w.length - 1; p++) {
    const a = w[p], b = w[p + 1];
    if (JOIN_NEXT.has(a) && AR_LETTERS.has(b) && !(a === 'ل' && 'اأإآ'.includes(b))) c.push(p);
  }
  return c;
}
function kashida(text, level) {
  if (level <= 0 || !hasAr(text)) return text;
  const words = text.split(' ');
  const idx = words.map((w, i) => hasAr(w) ? i : -1).filter(i => i >= 0);
  if (!idx.length) return text;
  let targets, nTat;
  if (level === 1) { targets = [idx.reduce((a, b) => words[b].length > words[a].length ? b : a)]; nTat = 3; }
  else if (level === 2) { targets = idx.filter(i => words[i].length >= 4); if (!targets.length) targets = idx; nTat = 2; }
  else { targets = idx.filter(i => words[i].length >= 3); if (!targets.length) targets = idx; nTat = 3; }
  for (const i of targets) {
    let w = words[i]; const cands = candPositions(w); if (!cands.length) continue;
    const tgt = Math.max(1, w.length * .35);
    const p = cands.reduce((a, b) => Math.abs(b - tgt) < Math.abs(a - tgt) ? b : a);
    const pos = [p];
    if (level === 3 && cands.length > 1) { const q = cands.reduce((a, b) => Math.abs(b - p) > Math.abs(a - p) ? b : a); if (Math.abs(q - p) >= 2) pos.push(q); }
    pos.sort((a, b) => b - a).forEach(pp => { w = w.slice(0, pp + 1) + 'ـ'.repeat(nTat) + w.slice(pp + 1); });
    words[i] = w;
  }
  if (!words.some(w => w.includes('ـ'))) {  // إلزامي
    for (const i of idx.slice().sort((a, b) => words[b].length - words[a].length)) {
      const c = candPositions(words[i]); if (c.length) { const p = c[0]; words[i] = words[i].slice(0, p + 1) + 'ـــ' + words[i].slice(p + 1); break; }
    }
  }
  return words.join(' ');
}

/* ---------------- كلمات مفتاحية ---------------- */
const TOPICS = [
  ['ألبان', /لبن|حليب|ألبان|البان|لبنية|زبادي|يوغرت|رايب|كريمة|قشطة|زبدة|milk|dairy/i],
  ['أجبان', /جبن|جبنة|فيتا|موزاريلا|رومي|شيدر|قريش|cheese/i],
  ['تصنيع', /مصنع|مصانع|إنتاج|انتاج|تصنيع|factory|مشروع/i],
  ['معدات', /ماكينة|ماكينات|معدات|آلة|الة|تشغيل|صيانة|هندسة|تكنولوجيا/i],
  ['تحليل', /تحليل|معمل|مختبر|فحص|اختبار|ميكروب|بكتيريا/i],
  ['بسترة', /حرارة|بسترة|تعقيم|تبريد|تسخين|درجة/i],
  ['نمو', /ربح|أرباح|ارباح|تكلفة|تكاليف|مبيعات|نجاح|نمو|سوق|تسويق|استثمار/i],
  ['جودة', /جودة|سلامة|معايير|شهادة|ايزو|haccp|أمان|امان|ترخيص/i],
];
function keywords(text, custom) {
  if (custom && custom.trim()) return custom.split(/[,،\n]/).map(s => s.trim()).filter(Boolean).slice(0, 4);
  const l = TOPICS.filter(([, re]) => re.test(text)).map(t => t[0]);
  for (const d of ['ألبان', 'تصنيع', 'جودة']) { if (l.length >= 3) break; if (!l.includes(d)) l.push(d); }
  return l.slice(0, 3);
}

/* ---------------- أدوات الرسم ---------------- */
const font = (s) => `700 ${s}px ${FONT}, Graphik, sans-serif`;
function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function cover(ctx, img, x, y, w, h, focus = [.5, .5]) {
  const iw = img.width, ih = img.height, s = Math.max(w / iw, h / ih), sw = w / s, sh = h / s;
  const sx = Math.min(Math.max(focus[0] * iw - sw / 2, 0), iw - sw), sy = Math.min(Math.max(focus[1] * ih - sh / 2, 0), ih - sh);
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
}
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function brandBg(ctx, W, H, frame) {
  const g = ctx.createLinearGradient(0, 0, W * .35, H * .95);
  g.addColorStop(0, '#35619E'); g.addColorStop(.34, '#24397D'); g.addColorStop(.66, '#192767'); g.addColorStop(1, '#121B52');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  if (frame) { ctx.save(); ctx.filter = 'blur(26px) saturate(.4)'; ctx.globalAlpha = .16; cover(ctx, frame, -40, -40, W + 80, H + 80); ctx.restore(); }
  const step = Math.min(W, H) / 11, r = rng(3);
  ctx.save(); ctx.strokeStyle = 'rgba(79,230,213,.09)'; ctx.lineWidth = 2;
  for (let x = 0; x < W; x += step) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += step) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  const n = Math.floor(W * H / 160000);
  for (let i = 0; i < n; i++) {
    const rad = step * (.25 + r() * .85), cx = r() * W, cy = r() * H;
    if (r() < .5) { ctx.strokeStyle = 'rgba(79,230,213,.19)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(cx, cy, rad, 0, 7); ctx.stroke(); }
    else { ctx.fillStyle = 'rgba(79,230,213,.10)'; ctx.beginPath(); ctx.arc(cx, cy, rad, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(cx, cy + rad * 2, rad, 0, 7); ctx.fill(); }
  }
  ctx.restore();
  const gl = ctx.createRadialGradient(W * .2, H * .13, 0, W * .2, H * .13, Math.min(W, H) * .6);
  gl.addColorStop(0, 'rgba(79,230,213,.3)'); gl.addColorStop(1, 'rgba(79,230,213,0)');
  ctx.fillStyle = gl; ctx.fillRect(0, 0, W, H);
}
function card(ctx, img, cx, cy, w, h, { radius = 28, bw = 6, angle = 0, focus = [.5, .5], shadow = true } = {}) {
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(angle * Math.PI / 180);
  const W2 = w + bw * 2, H2 = h + bw * 2;
  if (shadow) { ctx.shadowColor = 'rgba(3,8,30,.6)'; ctx.shadowBlur = 28; ctx.shadowOffsetY = 18; }
  ctx.fillStyle = TEAL; rr(ctx, -W2 / 2, -H2 / 2, W2, H2, radius + bw); ctx.fill();
  ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
  rr(ctx, -w / 2, -h / 2, w, h, radius); ctx.clip();
  cover(ctx, img, -w / 2, -h / 2, w, h, focus);
  ctx.restore();
}
function gradH(ctx, W, H, side, a0, a1, color = NAVY) {
  // side: 'left'|'right' كثافة من جهة، 'bottom' من الأسفل
  let g;
  if (side === 'bottom') { g = ctx.createLinearGradient(0, H * .7, 0, H); } else if (side === 'right') { g = ctx.createLinearGradient(W * .2, 0, W, 0); } else { g = ctx.createLinearGradient(W * .8, 0, 0, 0); }
  const c = (a) => color + Math.round(a * 255).toString(16).padStart(2, '0');
  g.addColorStop(0, c(0)); g.addColorStop(1, c(a1)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function chip(ctx, label, cx, cy, size) {
  ctx.font = font(size); ctx.direction = 'rtl';
  const tw = ctx.measureText(label).width, h = size * 1.95, dot = size * .5, w = tw + size * 1.7 + dot, x = cx - w / 2, y = cy - h / 2;
  ctx.save(); ctx.shadowColor = 'rgba(3,8,30,.45)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 8;
  ctx.fillStyle = 'rgba(15,25,79,.92)'; rr(ctx, x, y, w, h, h / 2); ctx.fill(); ctx.restore();
  ctx.strokeStyle = TEAL; ctx.lineWidth = 3; rr(ctx, x, y, w, h, h / 2); ctx.stroke();
  ctx.fillStyle = TEAL; ctx.beginPath(); ctx.arc(x + w - size * .75, cy, dot / 2, 0, 7); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(label, x + size * .7, cy + size * .06);
  return w;
}
function chipRow(ctx, labels, cx, cy, size, gap = 18) {
  ctx.font = font(size);
  const ws = labels.map(l => ctx.measureText(l).width + size * 1.7 + size * .5), total = ws.reduce((a, b) => a + b, 0) + gap * (labels.length - 1);
  let x = cx + total / 2;
  labels.forEach((l, i) => { chip(ctx, l, x - ws[i] / 2, cy, size); x -= ws[i] + gap; });
}
function chipCol(ctx, labels, cx, y0, size, gap = 18) {
  let y = y0; const h = size * 1.95;
  labels.forEach(l => { chip(ctx, l, cx, y + h / 2, size); y += h + gap; });
}

/* ---------------- العنوان بخط Handicrafts + تمديد + ستايل طبقات ---------------- */
const lerp = (a, b, t) => { const p = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)); const A = p(a), B = p(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`; };
function wrapLines(ctx, text, size, maxW) {
  ctx.font = font(size); const lines = []; let cur = '';
  for (const w of text.split(/\s+/).filter(Boolean)) { const t = cur ? cur + ' ' + w : w; if (ctx.measureText(t).width <= maxW || !cur) cur = t; else { lines.push(cur); cur = w; } }
  if (cur) lines.push(cur); return lines;
}
function drawTitle(ctx, text, box, maxSize, align, subtitle, anchor, kash, styleIdx) {
  text = kashida(text, kash);
  const st = STYLES[styleIdx], [x0, y0, x1, y1] = box;
  ctx.direction = 'rtl';
  const subSize = Math.max(32, Math.floor(maxSize * .27)), subH = subtitle ? Math.floor(subSize * 1.55) + 40 : 0;
  let size = maxSize, lines, lh;
  for (; size >= 50; size -= 4) { lines = wrapLines(ctx, text, size, x1 - x0); lh = Math.floor(size * 1.12); if (lines.length <= 3 && lines.length * lh <= (y1 - y0) - subH) break; }
  lines = wrapLines(ctx, text, size, x1 - x0).slice(0, 3); lh = Math.floor(size * 1.12);
  const total = lines.length * lh, block = total + subH;
  let y = anchor === 'top' ? y0 : anchor === 'bottom' ? y1 - block : y0 + ((y1 - y0) - block) / 2; y = Math.floor(y);
  const stroke = Math.max(6, Math.floor(size / 10)), depth = Math.max(8, Math.floor(Math.floor(size / 8) * st.depth)), dx = st.dx;
  ctx.font = font(size); ctx.lineJoin = 'round'; ctx.textBaseline = 'alphabetic';
  const ax = align === 'right' ? x1 : align === 'left' ? x0 : (x0 + x1) / 2;
  ctx.textAlign = align === 'right' ? 'right' : align === 'left' ? 'left' : 'center';
  const base = i => y + i * lh + size * .86;
  // وهج + ظل
  ctx.save(); ctx.shadowColor = st.glow; ctx.shadowBlur = size / 3 * 1.5; ctx.globalAlpha = st.glowA;
  ctx.strokeStyle = st.outline2 || st.outline; ctx.lineWidth = (stroke + (st.outline2 ? Math.max(6, stroke * .75) : 0)) * 2;
  lines.forEach((l, i) => ctx.strokeText(l, ax, base(i))); ctx.restore();
  ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.65)'; ctx.shadowBlur = 14; ctx.shadowOffsetX = -4; ctx.shadowOffsetY = depth + 16;
  ctx.strokeStyle = '#000'; ctx.lineWidth = (stroke + (st.outline2 ? Math.max(6, stroke * .75) : 0)) * 2;
  lines.forEach((l, i) => ctx.strokeText(l, ax, base(i))); ctx.restore();
  lines.forEach((l, i) => {
    const key = (i === lines.length - 1 && lines.length > 1), b = base(i);
    if (st.outline2) { ctx.strokeStyle = st.outline2; ctx.lineWidth = (stroke + Math.max(6, stroke * .75)) * 2; for (let k = 0; k <= depth; k++) ctx.strokeText(l, ax + k * dx, b + k); }
    ctx.strokeStyle = st.outline; ctx.lineWidth = stroke * 2; for (let k = 0; k <= depth; k++) ctx.strokeText(l, ax + k * dx, b + k);
    const [far, near] = key ? st.kext : st.ext;
    for (let k = depth; k > 0; k--) { ctx.fillStyle = lerp(far, near, (depth - k) / Math.max(1, depth - 1)); ctx.fillText(l, ax + k * dx, b + k); }
    const [c0, c1] = key ? st.kface : st.face, g = ctx.createLinearGradient(0, b - size * .7, 0, b + size * .1);
    g.addColorStop(0, c0); g.addColorStop(1, c1); ctx.fillStyle = g; ctx.fillText(l, ax, b);
  });
  if (subtitle) {
    ctx.font = font(subSize); const w = ctx.measureText(subtitle).width, pad = 26, bw = w + pad * 2, bh = Math.floor(subSize * 1.55), by = y + total + depth + 18;
    const bx = align === 'right' ? x1 - bw : align === 'left' ? x0 : (x0 + x1) / 2 - bw / 2;
    ctx.fillStyle = NAVY; rr(ctx, bx, by + 6, bw, bh, bh / 2); ctx.fill();
    ctx.fillStyle = TEAL; rr(ctx, bx, by, bw, bh, bh / 2); ctx.fill();
    ctx.fillStyle = NAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(subtitle, bx + bw / 2, by + bh / 2 + subSize * .06);
  }
}

/* ---------------- التركيبات ---------------- */
function makeLandscape(cv, frame, extras, o, focus, styleIdx) {
  const W = 1280, H = 720, ctx = cv.getContext('2d'); const rtl = o.title ? hasAr(o.title) : true;
  ctx.clearRect(0, 0, W, H);
  if (o.land === 'design') {
    brandBg(ctx, W, H, frame);
    const cx = rtl ? 370 : W - 370;
    card(ctx, frame, cx, 315, 640, 440, { radius: 30, bw: 7, angle: rtl ? -2 : 2, focus });
    if (o.kws.length) chipRow(ctx, o.kws, cx, 640, 34);
    if (o.title) drawTitle(ctx, o.title, rtl ? [W - 590, 80, W - 45, 640] : [45, 80, 590, 640], 175, rtl ? 'right' : 'left', o.subtitle, 'middle', o.kash, styleIdx);
    return;
  }
  ctx.save(); ctx.filter = 'contrast(1.1) saturate(1.15)'; cover(ctx, frame, 0, 0, W, H, focus); ctx.restore();
  let side = rtl ? 'right' : 'left'; if (o.focusSet) side = focus[0] > .55 ? 'left' : (focus[0] < .45 ? 'right' : side);
  gradH(ctx, W, H, side === 'right' ? 'left' : 'right', 0, .94); gradH(ctx, W, H, 'bottom', 0, .6);
  ctx.fillStyle = TEAL; ctx.fillRect(side === 'right' ? W - 16 : 0, 0, 16, H);
  if (o.kws.length) chipCol(ctx, o.kws, side === 'left' ? W - 160 : 160, 70, 34);
  if (o.title) drawTitle(ctx, o.title, side === 'right' ? [W - 740, 70, W - 55, H - 60] : [55, 70, 740, H - 60], 185, side === 'right' ? 'right' : 'left', o.subtitle, 'bottom', o.kash, styleIdx);
}
function makeStory(cv, frame, extras, o, focus, styleIdx) {
  const W = 1080, H = 1920, ctx = cv.getContext('2d'); ctx.clearRect(0, 0, W, H);
  if (o.mode === 'design') {
    brandBg(ctx, W, H, frame);
    const top = 850, hh = 700, gap = 24, fh = Math.floor((hh - 2 * gap) / 3);
    for (let i = 0; i < 3; i++) card(ctx, extras[i] || frame, 170, top + i * (fh + gap) + fh / 2, 190, fh - 12, { radius: 22, bw: 5 });
    card(ctx, frame, 651, top + hh / 2, 690, hh - 12, { radius: 34, bw: 8, focus });
    if (o.kws.length) chipRow(ctx, o.kws, W / 2, 790, 38);
    if (o.title) drawTitle(ctx, o.title, [60, 255, W - 60, 740], 200, 'center', o.subtitle, 'middle', o.kash, styleIdx);
    return;
  }
  if (o.mode === 'crop') { ctx.save(); ctx.filter = 'contrast(1.1) saturate(1.15)'; cover(ctx, frame, 0, 0, W, H, focus); ctx.restore(); }
  else { brandBg(ctx, W, H, frame); const w = W - 80, h = w * frame.height / frame.width; card(ctx, frame, W / 2, H * .5, w, h, { radius: 30, bw: 7 }); }
  gradH(ctx, W, H, 'bottom', 0, .92);
  const g = ctx.createLinearGradient(0, H * .45, 0, H); g.addColorStop(0, 'rgba(15,25,79,0)'); g.addColorStop(1, 'rgba(15,25,79,.92)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  if (o.title) drawTitle(ctx, o.title, [60, 1040, W - 60, H - 360], 190, 'center', o.subtitle, 'bottom', o.kash, styleIdx);
}

/* ---------------- تحليل الفيديو ---------------- */
const S = { video: null, stem: 'video', cands: [], sel: 0, focus: [.5, .45], focusSet: false, dur: 0, last: null };
const N = 24;
const seek = (v, t) => new Promise((res, rej) => { const ok = () => { v.removeEventListener('seeked', ok); res(); }; v.addEventListener('seeked', ok); v.currentTime = t; setTimeout(res, 4000); });
function msg(t, e) { $('msg').textContent = t; $('msg').className = e ? 'err' : ''; }
function score(cv) {
  const w = 160, h = Math.round(160 * cv.height / cv.width), c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d'); x.drawImage(cv, 0, 0, w, h); const d = x.getImageData(0, 0, w, h).data, g = new Float32Array(w * h);
  let sum = 0; for (let i = 0; i < w * h; i++) { g[i] = .299 * d[i * 4] + .587 * d[i * 4 + 1] + .114 * d[i * 4 + 2]; sum += g[i]; }
  const mean = sum / (w * h); let sd = 0, lap = 0, ln = 0;
  for (let i = 0; i < w * h; i++) sd += (g[i] - mean) ** 2; sd = Math.sqrt(sd / (w * h));
  for (let y = 1; y < h - 1; y++) for (let xx = 1; xx < w - 1; xx++) { const i = y * w + xx, l = 4 * g[i] - g[i - 1] - g[i + 1] - g[i - w] - g[i + w]; lap += l * l; ln++; }
  const sharp = Math.min(lap / ln / 300, 1), bright = 1 - Math.min(Math.abs(mean / 255 - .45) / .45, 1), contrast = Math.min(sd / 70, 1);
  return sharp * .4 + bright * .3 + contrast * .3;
}
async function analyze(src, stem) {
  const v = document.createElement('video'); v.muted = true; v.preload = 'auto'; v.playsInline = true; v.crossOrigin = 'anonymous'; v.src = src;
  await new Promise((res, rej) => { v.onloadedmetadata = res; v.onerror = () => rej(new Error('تعذر قراءة الفيديو (صيغة غير مدعومة أو الرابط لا يسمح)')); });
  if (!isFinite(v.duration) || v.duration <= 0) throw new Error('تعذر قراءة مدة الفيديو');
  S.video = v; S.stem = stem; S.dur = v.duration; S.cands = [];
  const t0 = v.duration * .06, t1 = v.duration * .95;
  for (let i = 0; i < N; i++) {
    const t = t0 + (t1 - t0) * i / (N - 1); await seek(v, t);
    const cv = document.createElement('canvas'), sc = Math.min(1, 960 / v.videoWidth); cv.width = Math.round(v.videoWidth * sc); cv.height = Math.round(v.videoHeight * sc);
    cv.getContext('2d').drawImage(v, 0, 0, cv.width, cv.height);
    S.cands.push({ i, t, cv, score: score(cv), url: cv.toDataURL('image/jpeg', .7) });
    $('bar1i').style.width = Math.round((i + 1) / N * 100) + '%'; msg(`بنستخرج اللقطات… ${i + 1}/${N}`);
  }
  S.sel = S.cands.reduce((a, b) => b.score > a.score ? b : a).i;
}
async function hiFrame(c) {
  const v = S.video; await seek(v, c.t); const sc = Math.min(1, 1920 / v.videoWidth), cv = document.createElement('canvas');
  cv.width = Math.round(v.videoWidth * sc); cv.height = Math.round(v.videoHeight * sc); cv.getContext('2d').drawImage(v, 0, 0, cv.width, cv.height); return cv;
}
function pickExtras(chosen, n = 3) {
  const gap = Math.max(3, S.dur * .08), taken = [chosen.t], out = [];
  for (const c of S.cands.slice().sort((a, b) => b.score - a.score)) { if (taken.every(t => Math.abs(c.t - t) >= gap)) { out.push(c.cv); taken.push(c.t); } if (out.length >= n) break; }
  return out;
}

/* ---------------- الواجهة ---------------- */
const dz = $('dz');
$('file').onchange = () => { const f = $('file').files[0]; if (f) { $('fname').textContent = '📁 ' + f.name; $('url').value = ''; } };
['dragover', 'dragenter'].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.add('over'); }));
['dragleave', 'drop'].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.remove('over'); }));
dz.addEventListener('drop', ev => { if (ev.dataTransfer.files[0]) { $('file').files = ev.dataTransfer.files; $('file').onchange(); } });
$('url').addEventListener('input', () => $('drivenote').classList.toggle('hide', !/drive\.google|docs\.google/i.test($('url').value)));

$('go').onclick = async () => {
  const f = $('file').files[0], u = $('url').value.trim();
  if (!f && !u) return msg('اسحب الفيديو أو الصق رابط مباشر', 1);
  if (/drive\.google|docs\.google/i.test(u) && !f) return msg('ده رابط درايف: نزّل الفيديو على جهازك واسحبه فوق', 1);
  $('go').disabled = true; $('bar1i').style.width = '0'; msg('بنجهّز الفيديو…');
  try {
    await document.fonts.load(`700 100px ${FONT}`); await document.fonts.load('700 20px Graphik');
    await analyze(f ? URL.createObjectURL(f) : u, f ? f.name.replace(/\.[^.]+$/, '') : 'thumbnail');
    $('grid').innerHTML = '';
    const best = S.cands.reduce((a, b) => b.score > a.score ? b : a).i;
    S.cands.forEach(c => { const el = document.createElement('div'); el.dataset.i = c.i; el.innerHTML = `<img src="${c.url}"><span>${c.i === best ? '⭐ ' : ''}${c.t.toFixed(1)}s</span>`; el.onclick = () => sel(c.i); $('grid').appendChild(el); });
    sel(best); $('c2').classList.remove('hide'); msg('تم ✔ اختر لقطة وأكمل'); $('c2').scrollIntoView({ behavior: 'smooth' });
  } catch (e) { msg(e.message, 1); }
  $('go').disabled = false;
};
function sel(i) {
  S.sel = i; document.querySelectorAll('#grid div').forEach(x => x.classList.toggle('sel', +x.dataset.i === i));
  $('fimg').src = S.cands[i].url; S.focus = [.5, .45]; S.focusSet = false; $('fdot').style.display = 'none';
}
$('focus').addEventListener('click', ev => {
  const r = $('fimg').getBoundingClientRect(); S.focus = [(ev.clientX - r.left) / r.width, (ev.clientY - r.top) / r.height]; S.focusSet = true;
  const d = $('fdot'); d.style.display = 'block'; d.style.left = (ev.clientX - r.left + $('fimg').offsetLeft) + 'px'; d.style.top = (ev.clientY - r.top + $('fimg').offsetTop) + 'px';
});

async function render() {
  $('render').disabled = true; $('msg3').className = ''; $('msg3').textContent = 'بنصمّم…';
  try {
    await document.fonts.load(`700 100px ${FONT}`); await document.fonts.load('700 20px Graphik');
    const c = S.cands[S.sel], frame = await hiFrame(c), extras = pickExtras(c, 3), kwv = $('kw').value.trim();
    const o = { title: $('title').value.trim(), subtitle: $('subtitle').value.trim(), kash: Math.max(1, +$('kash').value), land: $('land').value, mode: $('mode').value, focusSet: S.focusSet,
      kws: kwv === '-' ? [] : keywords(($('title').value + ' ' + $('subtitle').value), kwv) };
    const si = pickStyle(+$('style').value);
    makeLandscape($('cvL'), frame, extras, o, S.focus, si); makeStory($('cvS'), frame, extras, o, S.focus, si);
    $('stname').textContent = `· ستايل العنوان: ${STYLES[si].name} (${si + 1}/${STYLES.length})`;
    const blobs = await Promise.all([$('cvL'), $('cvS')].map(cv => new Promise(r => { let q = .94; const t = () => cv.toBlob(b => { if (b.size > 1.95e6 && q > .6) { q -= .08; t(); } else r(b); }, 'image/jpeg', q); t(); })));
    S.last = blobs; const names = [`${S.stem}_youtube_1280x720.jpg`, `${S.stem}_story_1080x1920.jpg`];
    [['dl', 0], ['ds', 1]].forEach(([id, k]) => { const a = $(id); if (a.href) URL.revokeObjectURL(a.href); a.href = URL.createObjectURL(blobs[k]); a.download = names[k]; });
    S.names = names; $('c3').classList.remove('hide'); $('msg3').textContent = ''; $('c3').scrollIntoView({ behavior: 'smooth' });
  } catch (e) { $('msg3').textContent = e.message; $('msg3').className = 'err'; console.error(e); }
  $('render').disabled = false;
}
$('render').onclick = render;
$('restyle').onclick = () => { $('style').value = '-1'; render(); };
$('newv').onclick = () => location.reload();
$('pickbtn').onclick = async () => {
  if (!S.last) return;
  if (!window.showDirectoryPicker) { $('saved').textContent = 'المتصفح لا يدعم اختيار الفولدر، استخدم روابط التحميل (Chrome/Edge).'; return; }
  try {
    const dir = await window.showDirectoryPicker({ mode: 'readwrite' });
    for (let k = 0; k < 2; k++) { const fh = await dir.getFileHandle(S.names[k], { create: true }), w = await fh.createWritable(); await w.write(S.last[k]); await w.close(); }
    $('saved').textContent = '✅ اتحفظت في: ' + dir.name;
  } catch (e) { if (e.name !== 'AbortError') $('saved').textContent = 'تعذر الحفظ: ' + e.message + ' — جرّب فولدر فرعي بدل Downloads/Documents.'; }
};
