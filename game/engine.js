/* 재의 백작 — 비주얼 노벨 엔진
 * story.json(ops)을 순서대로 실행하고, 자유 입력 이벤트는 로컬 Laya 서버(/api/judge)로 판정한다.
 */
"use strict";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// 판정 API 위치: ?api=<url>로 지정 > GitHub Pages면 REMOTE_API > 그 외에는 같은 서버(server/app.py)
// REMOTE_API가 비어 있으면 GitHub Pages에서는 브라우저 간이 판정(localJudge)으로 진행한다
const REMOTE_API = "";
const API_BASE = new URLSearchParams(location.search).get("api")
  ?? (location.hostname.endsWith("github.io") ? REMOTE_API : "");
const api = (path) => (API_BASE ? new URL(path, API_BASE).href : path);

const CHARS = {
  yuri: { name: "한유리", short: "유리", color: "var(--c-yuri)", init: 30 },
  dohyun: { name: "서도현", short: "도현", color: "var(--c-dohyun)", init: 30 },
  eunchae: { name: "마은채", short: "은채", color: "var(--c-eunchae)", init: 28 },
  seungha: { name: "백승하", short: "승하", color: "var(--c-seungha)", init: 25 },
  haram: { name: "진하람", short: "하람", color: "var(--c-haram)", init: 40 },
};
const MINOR_COLOR = { sion: "var(--c-sion)", gyeonghan: "#9a8f7e", baek: "#8a6d2a", jang: "#5d5d5d", ma: "#7d7f8a", butler: "#8e8170", mom: "#a99a8c" };
// 개별 이미지가 없을 때 공용 실루엣(characters/silhouette*.png)을 쓰는 조연 — 정장 남성 실루엣이라 어머니는 제외
const SILHOUETTE_CAST = new Set(["gyeonghan", "baek", "jang", "ma", "butler"]);
const EXPR_KO = { neutral: "평온", smile: "미소", sad: "슬픔", angry: "분노", surprised: "놀람", cold: "냉담", cry: "눈물", shy: "수줍음", pin: "머리핀", smirk: "비웃음", knife: "칼", usb: "USB", wet: "젖은" };
const POS = { left: 24, center: 50, right: 76 };
// 스탠딩 배치 — 상반신 구도. 가장 큰 인물의 정수리가 HEAD_TOP, 머리 길이가 HEAD(화면 높이 %)가 되도록
// 키우고, 대사창 윗선(--tb-top) 아래는 잘라낸다. 키 차이는 실제 비율대로 하면 너무 벌어지므로
// 1cm당 DROP%만 낮추고, 머리 크기도 SHRINK 비율만큼만 줄인다.
// cm: 설정상 키 / crown·chin: 원본 이미지에서 정수리·턱 위치(이미지 높이 대비 비율)
// expr: 구도가 다른 표정 이미지만 crown·chin을 따로 지정
const STATURE = {
  dohyun: { cm: 182, crown: 0.045, chin: 0.195 }, // 뻗친 머리카락은 제외한 두개골 기준 정수리
  seungha: { cm: 180, crown: 0.10, chin: 0.32 },
  eunchae: { cm: 167, crown: 0.04, chin: 0.235 }, // 고개를 숙인 포즈라 머리카락 끝이 아닌 두개골 기준 정수리
  yuri: { cm: 161, crown: 0.02, chin: 0.30 },
  haram: { cm: 154, crown: 0.05, chin: 0.28 },
  silhouette: { cm: 176, crown: 0.01, chin: 0.19 },
  mom: { cm: 158 },
};
const HEAD_TOP = 88; // 가장 큰 인물의 정수리 높이(화면 높이 %, 아래에서부터)
const HEAD = 18; // 가장 큰 인물의 머리 길이(화면 높이 %)
const DROP = 0.3; // 키 1cm 차이당 정수리를 낮추는 정도(화면 높이 %)
const SHRINK = 0.5; // 키에 비례한 머리 크기 축소를 얼마나 반영할지(0~1)
const TALLEST = Math.max(...Object.values(STATURE).map((s) => s.cm));
let CLIP = null;
function spriteFit(key, hasImage, expr) {
  const base = STATURE[key];
  if (!base) return null;
  const s = { ...base, ...base.expr?.[expr] };
  CLIP ??= parseFloat(getComputedStyle($("#stage")).getPropertyValue("--tb-top")) || 28.5;
  const diff = TALLEST - s.cm;
  const crownY = HEAD_TOP - DROP * diff;
  if (!hasImage || s.crown == null) return { height: crownY - CLIP + 9, bottom: CLIP - 5 }; // 플레이스홀더: 정수리 높이만 맞춘다
  const height = (HEAD * (1 - SHRINK * diff / TALLEST)) / (s.chin - s.crown);
  // 이미지가 짧아 하단이 대사창 위로 떠오르면 그만큼 내린다
  return { height, bottom: Math.min(CLIP, crownY + s.crown * height - height) };
}
const ENDINGS = [
  ["end_true", "TRUE · 새벽의 등대"],
  ["end_happy", "HAPPY · 봄의 귀환"],
  ["end_normal", "NORMAL · 백작의 퇴장"],
  ["end_bad_ashes", "BAD · 재의 백작"],
  ["end_bad_blade", "BAD · 칼끝"],
];
const DEBUG = new URLSearchParams(location.search).has("debug");

// ------------------------------------------------------------------ 상태
let STORY = null;
let st = null; // 진행 상태 (세이브 대상)
let runId = 0;
let mode = { auto: false, skip: false };
const opts = Object.assign(
  { speed: 70, auto: 45, vol: 60, voice: 80, hearts: true, detail: DEBUG },
  safeGet("coa_opts", {})
);

function newState() {
  const aff = {};
  for (const [k, c] of Object.entries(CHARS)) aff[k] = c.init;
  return { pc: 0, cur: 0, aff, flags: {}, venge: [], last: 0, bg: "black", cg: null, sprites: {}, bgm: null, chapter: "", log: [], judged: [] };
}

function safeGet(key, dflt) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : dflt; } catch { return dflt; }
}
function safeSet(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch { /* 저장 불가 환경 */ }
}

// ------------------------------------------------------------------ 에셋
const assetCache = new Map();
function probe(url) {
  if (assetCache.has(url)) return assetCache.get(url);
  const p = new Promise((res) => {
    const img = new Image();
    img.onload = () => res(url);
    img.onerror = () => res(null);
    img.src = url;
  });
  assetCache.set(url, p);
  return p;
}
let MANIFEST = null; // data/assets.json (서버가 시작할 때 생성)
async function findImage(dir, name) {
  if (MANIFEST) {
    for (const ext of ["webp", "png", "jpg", "jpeg"]) if (MANIFEST.has(`${dir}/${name}.${ext}`)) return `assets/${dir}/${name}.${ext}`;
    return null;
  }
  for (const ext of ["webp", "png", "jpg"]) {
    const hit = await probe(`assets/${dir}/${name}.${ext}`);
    if (hit) return hit;
  }
  return null;
}

function bgGradient(key) {
  const k = key || "black";
  if (k === "black") return "#000";
  if (k === "white") return "#f4f1ec";
  const has = (...w) => w.some((x) => k.includes(x));
  if (has("fire")) return "radial-gradient(ellipse at 50% 100%, #ff7a2f 0%, #8a1d0a 35%, #1a0605 75%)";
  if (has("rain")) return "linear-gradient(180deg, #2b3440, #151a21 60%, #0a0c10)";
  if (has("dawn", "spring")) return "linear-gradient(180deg, #f2b8a2 0%, #9a8fb8 45%, #3d4a6b 100%)";
  if (has("dusk")) return "linear-gradient(180deg, #f08a4b 0%, #8b3f5c 45%, #2a1c33 100%)";
  if (has("night", "dark", "sea", "breakwater", "deck", "ruins")) return "linear-gradient(180deg, #0f1a2e 0%, #0a1020 55%, #04060b 100%)";
  if (has("court", "detention", "hospital", "nursing", "infirmary", "columbarium")) return "linear-gradient(180deg, #4b5258, #2b3034 60%, #16191b)";
  if (has("party", "ceremony", "press")) return "radial-gradient(ellipse at 50% 30%, #6b5530, #2a2016 60%, #0e0b08)";
  if (has("smoke")) return "linear-gradient(180deg, #4a4340, #2a2422 60%, #120f0e)";
  if (has("mansion", "study", "chess")) return "linear-gradient(180deg, #3b2a22, #1e1612 60%, #0c0907)";
  return "linear-gradient(180deg, #6d6a66 0%, #3e3b38 55%, #1d1b1a 100%)"; // 낮/교내
}

async function setBg(key, instant = false) {
  st.bg = key;
  const url = await findImage("bg", key);
  const next = $("#bg-next");
  next.className = "layer" + (url ? "" : " ph-bg");
  next.dataset.key = key === "black" ? "" : key;
  next.style.background = url ? `center/cover no-repeat url("${url}")` : bgGradient(key);
  if (instant || mode.skip) {
    copyBg(next);
    return;
  }
  next.style.opacity = 1;
  await sleep(900);
  copyBg(next);
}
function copyBg(next) {
  const bg = $("#bg");
  bg.className = next.className;
  bg.dataset.key = next.dataset.key;
  bg.style.background = next.style.background;
  next.style.transition = "none";
  next.style.opacity = 0;
  void next.offsetWidth;
  next.style.transition = "";
}

async function setCg(key) {
  st.cg = key;
  const el = $("#cg");
  if (!key) { el.classList.add("hidden"); return; }
  const url = await findImage("cg", key);
  el.className = "layer" + (url ? "" : " ph-bg");
  el.dataset.key = key;
  el.style.background = url ? `center/cover no-repeat url("${url}")` : "";
}

async function showSprite(char, expr, pos) {
  st.sprites[char] = { expr, pos };
  let el = document.querySelector(`.sprite[data-char="${char}"]`);
  const fresh = !el;
  if (fresh) {
    el = document.createElement("div");
    el.className = "sprite entering";
    el.dataset.char = char;
    $("#sprites").appendChild(el);
  }
  el.style.left = POS[pos] + "%";
  el.style.zIndex = pos === "center" ? 2 : 1;
  let url = await findImage("characters", `${char}_${expr}`);
  let shownExpr = expr;
  if (!url) { url = await findImage("characters", `${char}_neutral`); shownExpr = "neutral"; }
  let shared = false;
  if (!url && SILHOUETTE_CAST.has(char)) {
    url = (await findImage("characters", "silhouette_crop")) || (await findImage("characters", "silhouette"));
    shared = !!url;
  }
  if (url) {
    el.innerHTML = `<img src="${url}" alt="">`;
    // 공용 실루엣은 인물별 색 후광으로 구분
    if (shared) el.firstChild.style.filter = `drop-shadow(0 0 1.2em ${MINOR_COLOR[char]}) drop-shadow(0 0 0.3em ${MINOR_COLOR[char]})`;
  } else {
    const c = CHARS[char] ? CHARS[char].color : MINOR_COLOR[char] || "#777";
    const name = CHARS[char] ? CHARS[char].short : (STORY.speakers[char] || char);
    el.style.setProperty("--c", c);
    el.innerHTML = `<div class="ph"><b>${name}</b><i>${EXPR_KO[expr] || expr}</i></div>`;
  }
  const fit = spriteFit(shared ? "silhouette" : char, !!url, shownExpr);
  el.style.height = fit ? fit.height.toFixed(2) + "%" : "";
  el.style.bottom = fit ? fit.bottom.toFixed(2) + "%" : "";
  if (fresh) requestAnimationFrame(() => requestAnimationFrame(() => el.classList.remove("entering")));
}
function hideSprite(char) {
  if (char === "all") {
    st.sprites = {};
    $$(".sprite").forEach((e) => e.remove());
    return;
  }
  delete st.sprites[char];
  const el = document.querySelector(`.sprite[data-char="${char}"]`);
  if (el) { el.classList.add("entering"); setTimeout(() => el.remove(), 450); }
}
function focusSpeaker(who) {
  const any = $$(".sprite").some((e) => e.dataset.char === who);
  $$(".sprite").forEach((e) => e.classList.toggle("dim", any && e.dataset.char !== who));
}

// ------------------------------------------------------------------ 오디오
const audio = { bgm: new Audio(), key: null };
audio.bgm.loop = true;
const TITLE_BGM = "theme_ashes";
function setBgm(key) {
  st.bgm = key === "stop" ? null : key;
  playBgm(key);
}
function playBgm(key) {
  if (key === "stop" || !key) { audio.bgm.pause(); audio.key = null; return; }
  if (audio.key === key) return;
  audio.key = key;
  audio.bgm.src = `assets/bgm/${key}.mp3`;
  audio.bgm.volume = opts.vol / 100;
  audio.bgm.play().catch(() => {});
}
// 브라우저는 첫 사용자 입력 전 자동 재생을 막는다 → 막혔던 타이틀 BGM을 첫 입력 때 재생
function resumeBgmOnInput() {
  const resume = () => {
    if (audio.key && audio.bgm.paused) audio.bgm.play().catch(() => {});
    ["pointerdown", "keydown"].forEach((t) => window.removeEventListener(t, resume, true));
  };
  ["pointerdown", "keydown"].forEach((t) => window.addEventListener(t, resume, true));
}
// 대사 음성 (tools/gen_voices.py가 만든 assets/voice/…, story.json의 op.voice). 현재 음성 파일 없음 — docs/VOICE_REPORT.md
const voice = new Audio();
const hasVoice = () => (STORY?.stats?.voiced || 0) > 0;
// 음성이 있을 때만 크레딧에 표시. 음성을 다시 만들면 사용한 엔진에 맞게 고칠 것
const VOICE_CREDIT = "<p>This audio was created with Boson AI's Higgs Audio — boson.ai/higgs-audio</p><p>목소리 디자인 Qwen3-TTS VoiceDesign</p>";
function stopVoice() { voice.pause(); voice.removeAttribute("src"); }
function playVoice(rel) {
  stopVoice();
  if (!rel || mode.skip || !opts.voice) return;
  voice.src = `assets/${rel}`;
  voice.volume = opts.voice / 100;
  voice.play().catch(() => {});
}
// 자동 진행: 음성이 끝날 때까지 기다린다
function voiceDone() {
  if (!voice.src || voice.paused || voice.ended) return Promise.resolve();
  return new Promise((res) => {
    const end = () => { voice.removeEventListener("ended", end); voice.removeEventListener("pause", end); res(); };
    voice.addEventListener("ended", end);
    voice.addEventListener("pause", end);
  });
}
function playSfx(key) {
  if (mode.skip) return;
  const a = new Audio(`assets/sfx/${key}.mp3`);
  a.volume = opts.vol / 100;
  a.play().catch(() => {});
}

// ------------------------------------------------------------------ 효과
function fx(key) {
  const el = $("#fx");
  if (key === "shake") {
    const s = $("#stage");
    s.classList.remove("shake"); void s.offsetWidth; s.classList.add("shake");
  } else if (key === "flash" || key === "red") {
    el.className = "layer"; void el.offsetWidth; el.className = "layer " + key;
  } else if (key === "fadeout") {
    el.className = "layer black"; el.style.opacity = 1;
  } else if (key === "fadein") {
    el.style.opacity = 0; setTimeout(() => { el.className = "layer"; el.style.opacity = ""; }, 800);
  }
}
let emberTimer = null;
function embers(on) {
  clearInterval(emberTimer);
  if (!on) return;
  emberTimer = setInterval(() => {
    const e = document.createElement("div");
    e.className = "ember";
    e.style.left = Math.random() * 100 + "%";
    e.style.setProperty("--dx", (Math.random() * 30 - 15) + "cqw");
    e.style.animationDuration = 4 + Math.random() * 4 + "s";
    $("#embers").appendChild(e);
    setTimeout(() => e.remove(), 8000);
  }, 260);
}

// 타이틀: 장작불에서 튀어 오르는 아주 작은 불티들 (타이틀이 보일 때만 그림)
function titleSparks() {
  const cv = $("#title-sparks");
  const ctx = cv.getContext("2d");
  if (!ctx || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  let W = 0, H = 0, dpr = 1, last = 0, acc = 0, time = 0;
  const parts = [];
  const fit = () => {
    dpr = Math.min(devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  };
  new ResizeObserver(fit).observe(cv);
  const rnd = (a, b) => a + Math.random() * (b - a);
  const gauss = () => (Math.random() + Math.random() + Math.random() - 1.5) / 1.5; // -1..1, 가운데 몰림
  function spawn(burst) {
    const s = H / 540;
    // 화면 아래 가운데(불빛 아래)에 불이 있다고 보고 거기서 솟는다
    const x = W * (0.5 + gauss() * 0.42);
    const y = H * rnd(1.0, 1.06);
    const fast = burst || Math.random() < 0.18; // 탁 튀며 빠르게 솟는 불티
    parts.push({
      x, y,
      vx: rnd(-18, 18) * s * (fast ? 2.2 : 1),
      vy: -(fast ? rnd(230, 380) : rnd(60, 150)) * s,
      r: rnd(0.4, fast ? 1.0 : 1.4) * s,
      t: 0, life: fast ? rnd(0.9, 1.8) : rnd(2.2, 4.5),
      ph: Math.random() * 100, wob: rnd(10, 40) * s, fq: rnd(0.6, 1.8),
      fl: rnd(8, 20), hot: rnd(0.7, 1), fast,
    });
  }
  function frame(now) {
    requestAnimationFrame(frame);
    const dt = Math.min((now - last) / 1000, 0.05); last = now;
    if ($("#title").classList.contains("hidden") || !W) { parts.length = 0; return; }
    time += dt;
    acc += dt * rnd(10, 22);
    while (acc >= 1) { acc--; spawn(false); }
    // 장작이 가끔 탁 터지면 한꺼번에 여러 개가 솟는다
    if (Math.random() < dt * 0.5) for (let i = 4 + (Math.random() * 8 | 0); i--;) spawn(true);
    const s = H / 540;
    const wind = Math.sin(time * 0.37) * 14 * s + Math.sin(time * 1.1) * 6 * s; // 느린 바람
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    for (let i = parts.length - 1; i >= 0; i--) {
      const p = parts[i];
      p.t += dt;
      if (p.t >= p.life || p.y < -10) { parts.splice(i, 1); continue; }
      const drag = p.fast ? 1.6 : 0.6;
      p.vy = p.vy * (1 - drag * dt) - 35 * s * dt; // 뜨거운 공기에 실려 계속 떠오름
      p.vx = p.vx * (1 - drag * dt) + wind * dt * 1.5;
      const sway = Math.sin(time * p.fq * 6.28 + p.ph) * p.wob; // 하늘하늘 흔들림
      const py = p.y;
      p.x += p.vx * dt; p.y += p.vy * dt;
      const x = p.x + sway * Math.min(1, p.t * 1.5);
      const k = 1 - p.t / p.life; // 1 → 0 (식어 감)
      const flick = 0.65 + 0.35 * Math.sin(time * p.fl + p.ph) * Math.sin(time * p.fl * 0.53 + p.ph * 2);
      const a = Math.min(1, p.t * 6) * Math.pow(k, 0.7) * flick;
      const hue = 12 + 36 * k * p.hot, light = 48 + 42 * k * k * p.hot;
      if (p.fast && p.sxp !== undefined) { // 빠른 불티는 짧은 꼬리
        ctx.strokeStyle = `hsla(${hue},100%,${light}%,${a * 0.8})`;
        ctx.lineWidth = p.r * 1.6;
        ctx.beginPath(); ctx.moveTo(p.sxp, py + (py - p.y) * 1.5); ctx.lineTo(x, p.y); ctx.stroke();
      }
      p.sxp = x;
      ctx.fillStyle = `hsla(${hue},100%,${light}%,${a * 0.18})`; // 은은한 빛무리
      ctx.beginPath(); ctx.arc(x, p.y, p.r * 4, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `hsla(${hue + 8},100%,${Math.min(95, light + 15)}%,${a})`;
      ctx.beginPath(); ctx.arc(x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
  }
  requestAnimationFrame((t) => { last = t; frame(t); });
}

// ------------------------------------------------------------------ 텍스트
let advance = null; // 클릭 대기 resolver
let typing = null; // 타이핑 중이면 완료 함수

function speakerColor(who) {
  return CHARS[who] ? CHARS[who].color : MINOR_COLOR[who] || "var(--bone-dim)";
}

async function showLine(op, myRun) {
  const box = $("#textbox");
  box.classList.remove("hidden", "done");
  const isNarr = op.op === "narr";
  box.classList.toggle("narr", isNarr);
  const name = isNarr ? "" : op.name;
  $("#namebox").textContent = name;
  $("#namebox").style.setProperty("--nc", speakerColor(op.who));
  const text = isNarr ? op.text : `「${op.text}」`;
  st.log.push({ name, text });
  if (st.log.length > 200) st.log.shift();
  if (!isNarr) focusSpeaker(op.who);
  playVoice(op.voice);

  const el = $("#text");
  const cps = 12 + opts.speed * 1.6; // 초당 글자
  if (mode.skip || opts.speed >= 100) {
    el.textContent = text;
  } else {
    el.textContent = "";
    await new Promise((res) => {
      let i = 0;
      const timer = setInterval(() => {
        i += 1;
        el.textContent = text.slice(0, i);
        if (i >= text.length) finish();
      }, 1000 / cps);
      function finish() { clearInterval(timer); el.textContent = text; typing = null; res(); }
      typing = finish;
    });
  }
  if (myRun !== runId) return;
  box.classList.add("done");
  await waitAdvance(text.length);
}

function waitAdvance(len = 20) {
  return new Promise((res) => {
    advance = res;
    if (mode.skip) setTimeout(() => advance === res && (advance = null, res()), 40);
    else if (mode.auto) {
      const ms = 900 + len * (30 + (100 - opts.auto) * 0.9);
      const wait = Promise.all([sleep(ms), voiceDone().then(() => sleep(400))]);
      wait.then(() => advance === res && (advance = null, res()));
    }
  });
}

function userAdvance() {
  if (!st || anyOverlayOpen()) return;
  if (typing) { typing(); return; }
  if (advance) { const a = advance; advance = null; a(); }
}

function anyOverlayOpen() {
  return !$("#input-panel").classList.contains("hidden") || modalOpen();
}
// 입력 패널 위에 뜨는 창(로그·세이브·메뉴 등) — 자유 입력 중에도 열 수 있다
function modalOpen() {
  return ["#log", "#slots", "#menu", "#title", "#endings", "#credits"].some((s) => !$(s).classList.contains("hidden"));
}

// ------------------------------------------------------------------ 조건 / 엔딩
function vengeancePct() {
  if (!st.venge.length) return 0;
  const sw = st.venge.reduce((a, x) => a + x.w, 0);
  return Math.round((st.venge.reduce((a, x) => a + x.v * x.w, 0) / sw) * 100);
}
function evalCond(cond) {
  return cond.split(/\s*&&\s*/).every((c) => {
    c = c.trim();
    if (c.startsWith("!flag.")) return !st.flags[c.slice(6)];
    if (c.startsWith("flag.")) return !!st.flags[c.slice(5)];
    const m = c.match(/^(aff\.(\w+)|vengeance|last)\s*(>=|<=|==|!=|>|<)\s*(-?\d+)$/);
    if (!m) { console.warn("bad cond", c); return false; }
    const lhs = m[2] ? st.aff[m[2]] ?? 0 : m[1] === "vengeance" ? vengeancePct() : st.last;
    const rhs = Number(m[4]);
    return { ">=": lhs >= rhs, "<=": lhs <= rhs, "==": lhs === rhs, "!=": lhs !== rhs, ">": lhs > rhs, "<": lhs < rhs }[m[3]];
  });
}
function decideEnding() {
  const a = st.aff, v = vengeancePct();
  const others = ["yuri", "dohyun", "eunchae", "seungha"];
  if (v >= 60) return "end_bad_ashes";
  if (a.haram < 35) return "end_bad_blade";
  if (Object.values(a).every((x) => x >= 50) && a.haram >= 65 && v < 45) return "end_true";
  if (a.haram >= 55 && others.filter((k) => a[k] >= 45).length >= 3) return "end_happy";
  return "end_normal";
}

// ------------------------------------------------------------------ 판정
async function judge(ev, text) {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), API_BASE ? 20000 : 8000); // 원격(CPU) 서버는 판정이 수 초 걸린다
    const r = await fetch(api("api/judge"), {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ event_id: ev.id, text }), signal: ctrl.signal,
    });
    clearTimeout(t);
    if (r.ok) return await r.json();
  } catch { /* 서버 없음 → 대체 판정 */ }
  return localJudge(text);
}
function localJudge(text) {
  const hostile = (text.match(/닥쳐|꺼져|죽어|병신|씨발|시발|멍청|한심|불쌍|알 바|상관없/g) || []).length;
  const warm = (text.match(/미안|고마|괜찮|곁에|같이|함께|믿어|진심|들을게|기다릴/g) || []).length;
  const rev = (text.match(/복수|무너뜨|짓밟|대가|갚아|끝장|파멸|이용/g) || []).length;
  const junk = text.trim().length < 2 || !/[가-힣]/.test(text);
  let p = hostile > warm ? [0.55, 0.3, 0.1, 0.05, 0] : warm >= 2 ? [0, 0.05, 0.15, 0.45, 0.35] : warm ? [0, 0.1, 0.3, 0.45, 0.15] : [0.05, 0.25, 0.5, 0.15, 0.05];
  if (junk) p = [0.3, 0.5, 0.2, 0, 0];
  const w = [-12, -5, 0, 7, 13];
  let delta = p.reduce((a, x, i) => a + x * w[i], 0);
  if (junk) delta = Math.min(delta, 0) - 7;
  delta = Math.round(delta);
  return { impact: p, vengeance: Math.min(0.95, 0.1 + 0.35 * rev), nonsense: junk ? 0.9 : 0, delta,
    tier: delta <= -3 ? "low" : delta >= 5 ? "high" : "mid", model: "offline-heuristic", latency_ms: 0 };
}

let cancelAsk = null; // 입력 대기 중 로드/타이틀 이동 시 리스너 정리

function askPlayer(ev) {
  return new Promise((res) => {
    const panel = $("#input-panel");
    const target = CHARS[ev.target];
    panel.style.setProperty("--tc", target ? target.color : "var(--ember)");
    panel.querySelector(".target-name").textContent = target ? `${target.name}에게` : "마음속의 대답";
    panel.querySelector(".prompt").textContent = ev.prompt;
    // 직전 대사를 함께 보여 줘 상황을 놓치지 않게
    panel.querySelector(".recent").innerHTML = st.log.slice(-2).map((l) =>
      `<p>${l.name ? `<b>${escapeHtml(l.name)}</b>` : ""}${escapeHtml(l.text)}</p>`).join("");
    const hint = panel.querySelector(".hint");
    hint.textContent = ev.hint || "정답은 없다. 시온이라면 무슨 말을 할까.";
    hint.classList.add("hidden");
    panel.querySelector(".judging").classList.add("hidden");
    const ta = $("#player-line");
    ta.value = "";
    ta.disabled = false;
    $("#char-count").textContent = "0 / 300";
    $("#say-btn").disabled = true;
    panel.classList.remove("hidden");
    setTimeout(() => ta.focus(), 50);
    const submit = () => {
      const v = ta.value.trim();
      if (!v) return;
      ta.disabled = true;
      $("#say-btn").disabled = true;
      panel.querySelector(".judging").classList.remove("hidden");
      cleanup();
      res(v);
    };
    const onKey = (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); submit(); }
      else if (e.altKey && (e.key === "l" || e.key === "L")) { e.preventDefault(); openLog(); }
      else if (e.altKey && (e.key === "h" || e.key === "H")) { e.preventDefault(); $("#hearts").classList.toggle("hidden"); }
      e.stopPropagation();
    };
    const onInput = () => {
      $("#char-count").textContent = `${ta.value.length} / 300`;
      $("#say-btn").disabled = !ta.value.trim();
    };
    const onHint = () => hint.classList.remove("hidden");
    function cleanup() {
      cancelAsk = null;
      ta.removeEventListener("keydown", onKey);
      ta.removeEventListener("input", onInput);
      $("#say-btn").removeEventListener("click", submit);
      $("#hint-btn").removeEventListener("click", onHint);
      $("#input-log-btn").removeEventListener("click", openLog);
    }
    cancelAsk = () => { cleanup(); panel.classList.add("hidden"); };
    ta.addEventListener("keydown", onKey);
    ta.addEventListener("input", onInput);
    $("#say-btn").addEventListener("click", submit);
    $("#hint-btn").addEventListener("click", onHint);
    $("#input-log-btn").addEventListener("click", openLog);
  });
}

function popDelta(ev, r) {
  const el = $("#delta-pop");
  const t = CHARS[ev.target];
  const v = Math.round(r.vengeance * 100);
  let html = "";
  if (t && opts.hearts) {
    const sign = r.delta > 0 ? "+" : "";
    const col = r.delta > 0 ? t.color : r.delta < 0 ? "#8a8a8a" : "var(--bone-dim)";
    const word = r.delta >= 10 ? "마음이 크게 흔들렸다" : r.delta >= 5 ? "마음이 열렸다" : r.delta <= -8 ? "깊은 상처를 남겼다" : r.delta <= -3 ? "실망시켰다" : "잔잔하게 스쳐갔다";
    html = `<span style="color:${col}">${t.short} ♥ ${sign}${r.delta}</span><small>${word}</small>`;
  } else if (opts.hearts) {
    html = `<span style="color:var(--ember-2)">${v >= 50 ? "복수의 불씨가 타오른다" : "불씨가 잦아든다"}</span><small>복수심 ${v}%</small>`;
  }
  if (!html) return;
  el.innerHTML = html;
  el.classList.remove("hidden");
  el.style.animation = "none"; void el.offsetWidth; el.style.animation = "";
  setTimeout(() => el.classList.add("hidden"), 2700);
}

function showDetail(ev, text, r) {
  const el = $("#judge-detail");
  if (!opts.detail) { el.classList.add("hidden"); return; }
  const bars = r.impact.map((p, i) => `  L${i} ${"█".repeat(Math.round(p * 20)).padEnd(20, "·")} ${(p * 100).toFixed(0).padStart(3)}%`).join("\n");
  el.textContent = `Laya 판정 · ${ev.id} (${r.model}, ${r.latency_ms}ms)\n「${text.slice(0, 22)}${text.length > 22 ? "…" : ""}」\nimpact\n${bars}\nvengeance ${(r.vengeance * 100).toFixed(0)}%  nonsense ${(r.nonsense * 100).toFixed(0)}%\nΔ ${r.delta}  → ${r.tier}`;
  el.classList.remove("hidden");
}

async function runEvent(op, myRun) {
  const ev = { ...STORY.events[op.id], id: op.id };
  $("#textbox").classList.add("hidden");
  mode.skip = false; syncModeButtons();
  const text = await askPlayer(ev);
  if (myRun !== runId) return null;
  const r = await judge(ev, text);
  if (myRun !== runId) return null;
  $("#input-panel").classList.add("hidden");
  if (ev.target !== "none") st.aff[ev.target] = Math.max(0, Math.min(100, st.aff[ev.target] + r.delta));
  st.venge.push({ v: r.vengeance, w: op.id === "E17" ? 2 : 1 });
  st.last = r.delta;
  st.judged.push({ id: op.id, text, delta: r.delta, tier: r.tier });
  st.log.push({ name: "시온 (나)", text: `「${text}」`, player: true });
  popDelta(ev, r);
  showDetail(ev, text, r);
  renderHearts();
  return r.tier;
}

// ------------------------------------------------------------------ 실행 루프
async function run() {
  const myRun = ++runId;
  while (myRun === runId) {
    const pc = st.pc;
    const op = STORY.ops[pc];
    if (!op) { toTitle(); return; }
    st.pc = pc + 1;
    switch (op.op) {
      case "say":
      case "narr":
        st.cur = pc;
        await showLine(op, myRun);
        break;
      case "chapter":
        st.cur = pc;
        st.chapter = op.title;
        $("#chapter-label").textContent = op.title;
        await chapterCard(op.title, myRun);
        break;
      case "bg": await setBg(op.key); break;
      case "cg": await setCg(op.key === "off" ? null : op.key); break;
      case "show": await showSprite(op.char, op.expr, op.pos); break;
      case "hide": hideSprite(op.char); break;
      case "bgm":
        setBgm(op.key);
        embers(op.key === "fire");
        break;
      case "sfx": playSfx(op.key); break;
      case "fx": fx(op.key); break;
      case "wait": if (!mode.skip) await sleep(op.sec * 1000); break;
      case "aff": st.aff[op.char] = Math.max(0, Math.min(100, st.aff[op.char] + op.delta)); renderHearts(); break;
      case "flag": st.flags[op.key] = true; break;
      case "if": if (!evalCond(op.cond)) st.pc = op.else; break;
      case "goto": st.pc = op.to; break;
      case "jump": st.pc = STORY.labels[op.label]; break;
      case "event": {
        st.cur = pc;
        const tier = await runEvent(op, myRun);
        if (tier === null) return;
        st.pc = op.cases[tier];
        break;
      }
      case "ending": {
        const label = decideEnding();
        const seen = safeGet("coa_endings", {});
        seen[label] = Date.now();
        safeSet("coa_endings", seen);
        st.flags["ending_" + label] = true;
        st.pc = STORY.labels[label];
        break;
      }
      case "end":
        await credits(myRun);
        if (myRun === runId) toTitle();
        return;
      default:
        console.warn("unknown op", op);
    }
  }
}

async function chapterCard(title, myRun) {
  if (mode.skip) return;
  $("#textbox").classList.add("hidden");
  const card = $("#chapter-card");
  card.querySelector("h2").textContent = title;
  card.classList.remove("hidden");
  await sleep(2600);
  if (myRun === runId) card.classList.add("hidden");
}

async function credits(myRun) {
  $("#textbox").classList.add("hidden");
  embers(false);
  const el = $("#credits");
  const v = vengeancePct();
  const hearts = Object.entries(CHARS).map(([k, c]) => `<p>${c.name} — ${st.aff[k]}</p>`).join("");
  el.querySelector(".roll").innerHTML = `<h2>재의 백작</h2><p class="k">마음의 온도</p>${hearts}<p class="k">복수심</p><p>${v}%</p>
    <p class="k">판정</p><p>Laya (convaiinnovations/laya-multilingual, fine-tuned)</p>
    ${hasVoice() ? `<p class="k">음성</p>${VOICE_CREDIT}` : ""}
    <p class="k">THANK YOU FOR PLAYING</p>`;
  el.classList.remove("hidden");
  await new Promise((res) => { const done = () => { el.removeEventListener("click", done); res(); }; el.addEventListener("click", done); setTimeout(done, 22000); });
  if (myRun === runId) el.classList.add("hidden");
}

// ------------------------------------------------------------------ 복원 (세이브 로드)
async function restore(snapshot) {
  st = JSON.parse(JSON.stringify(snapshot));
  st.pc = st.cur;
  runId++;
  if (cancelAsk) cancelAsk();
  $("#input-panel").classList.add("hidden");
  $("#textbox").classList.add("hidden");
  const sprites = st.sprites;
  hideSprite("all");
  closeAll();
  $("#title").classList.add("hidden");
  $("#hud").classList.remove("hidden");
  $("#chapter-label").textContent = st.chapter || "";
  await setBg(st.bg || "black", true);
  await setCg(st.cg);
  for (const [c, s] of Object.entries(sprites)) await showSprite(c, s.expr, s.pos);
  setBgm(st.bgm);
  embers(st.bgm === "fire");
  renderHearts();
  run();
}

// ------------------------------------------------------------------ UI: 호감도 / 로그 / 슬롯 / 메뉴
function renderHearts() {
  if (!st) return;
  $("#heart-list").innerHTML = Object.entries(CHARS).map(([k, c]) =>
    `<div class="heart-row" style="--c:${c.color}"><span>${c.short}</span><div class="bar"><i style="width:${st.aff[k]}%"></i></div><b>${st.aff[k]}</b></div>`).join("");
  const v = vengeancePct();
  $("#hearts .venge i").style.width = v + "%";
  $("#hearts .venge b").textContent = v + "%";
}

function openLog() {
  $("#log-list").innerHTML = st.log.slice(-120).map((l) =>
    `<p class="${l.player ? "player" : ""}">${l.name ? `<b>${l.name}</b>` : ""}${escapeHtml(l.text)}</p>`).join("");
  $("#log").classList.remove("hidden");
  document.activeElement?.blur(); // 입력창에서 열었어도 Esc로 닫을 수 있게
  const s = $("#log .sheet"); s.scrollTop = s.scrollHeight;
}
function escapeHtml(s) { return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

function openSlots(kind) {
  $("#slots-title").textContent = kind === "save" ? "저장" : "불러오기";
  const saves = safeGet("coa_saves", {});
  const list = $("#slot-list");
  list.innerHTML = "";
  for (let i = 1; i <= 9; i++) {
    const s = saves[i];
    const b = document.createElement("button");
    b.className = "slot";
    b.innerHTML = s ? `<b>${i}. ${s.state.chapter || "프롤로그"}</b><span>${new Date(s.time).toLocaleString("ko-KR")}</span><span>${escapeHtml(s.preview)}</span>` : `<b>${i}. 빈 슬롯</b>`;
    b.onclick = () => {
      if (kind === "save") {
        const cur = STORY.ops[st.cur];
        saves[i] = { time: Date.now(), state: st, preview: (cur && cur.text ? cur.text : STORY.events[cur?.id]?.prompt || "").slice(0, 40) };
        safeSet("coa_saves", saves);
        openSlots("save");
      } else if (s) {
        restore(s.state);
      }
    };
    list.appendChild(b);
  }
  $("#slots").classList.remove("hidden");
}

function autosave() {
  if (st) safeSet("coa_auto", { time: Date.now(), state: st });
}

function openMenu() {
  $("#opt-speed").value = opts.speed;
  $("#opt-auto").value = opts.auto;
  $("#opt-vol").value = opts.vol;
  $("#opt-voice").value = opts.voice;
  $("#opt-voice").parentElement.classList.toggle("hidden", !hasVoice());
  $("#opt-hearts").checked = opts.hearts;
  $("#opt-detail").checked = opts.detail;
  $("#to-title").classList.toggle("hidden", !st || !$("#title").classList.contains("hidden"));
  $("#menu").classList.remove("hidden");
}
function saveOpts() {
  opts.speed = +$("#opt-speed").value;
  opts.auto = +$("#opt-auto").value;
  opts.vol = +$("#opt-vol").value;
  opts.voice = +$("#opt-voice").value;
  voice.volume = opts.voice / 100;
  opts.hearts = $("#opt-hearts").checked;
  opts.detail = $("#opt-detail").checked;
  audio.bgm.volume = opts.vol / 100;
  if (!opts.detail) $("#judge-detail").classList.add("hidden");
  safeSet("coa_opts", opts);
}

function closeAll() {
  ["#log", "#slots", "#menu", "#endings"].forEach((s) => $(s).classList.add("hidden"));
  const ta = $("#player-line");
  if (!$("#input-panel").classList.contains("hidden") && !ta.disabled) ta.focus();
}

function syncModeButtons() {
  document.querySelector('[data-act="auto"]').classList.toggle("on", mode.auto);
  document.querySelector('[data-act="skip"]').classList.toggle("on", mode.skip);
}

function toggleMode(m) {
  mode[m] = !mode[m];
  if (m === "auto" && mode.auto) mode.skip = false;
  if (m === "skip" && mode.skip) mode.auto = false;
  syncModeButtons();
  if ((mode.auto || mode.skip) && advance && !typing) userAdvance();
}

function toTitle() {
  runId++;
  if (cancelAsk) cancelAsk();
  autosave();
  mode = { auto: false, skip: false };
  syncModeButtons();
  embers(false);
  stopVoice();
  closeAll();
  ["#textbox", "#hud", "#hearts", "#judge-detail", "#input-panel", "#chapter-card", "#credits", "#cg"].forEach((s) => $(s).classList.add("hidden"));
  hideSprite("all");
  setBgm("stop");
  playBgm(TITLE_BGM);
  $("#title").classList.remove("hidden");
  $('[data-title="continue"]').disabled = !safeGet("coa_auto", null);
}

function openEndings() {
  const seen = safeGet("coa_endings", {});
  $("#ending-list").innerHTML = ENDINGS.map(([k, n]) =>
    `<div class="ending-row ${seen[k] ? "" : "locked"}"><span>${seen[k] ? n : "？？？"}</span><span>${seen[k] ? new Date(seen[k]).toLocaleDateString("ko-KR") : ""}</span></div>`).join("");
  $("#endings").classList.remove("hidden");
}

// ------------------------------------------------------------------ 입력 바인딩
function bind() {
  $("#textbox").addEventListener("click", userAdvance);
  $("#sprites").parentElement.addEventListener("click", (e) => {
    if (e.target.closest("button, .overlay, .panel, #textbox")) return;
    userAdvance();
  });
  $("#stage").addEventListener("wheel", (e) => {
    if (e.deltaY < 0 && st && $("#title").classList.contains("hidden") && !modalOpen() && !e.target.closest("#player-line, .recent")) openLog();
  });
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
    const inGame = st && $("#title").classList.contains("hidden");
    if (e.key === "Escape") {
      if (modalOpen() && $("#title").classList.contains("hidden")) { closeAll(); saveOpts(); }
      else if (inGame) openMenu();
      return;
    }
    if (!inGame) return;
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); userAdvance(); }
    else if (e.key === "h" || e.key === "H") $("#hearts").classList.toggle("hidden");
    else if (e.key === "l" || e.key === "L") openLog();
    else if (e.key === "a" || e.key === "A") toggleMode("auto");
    else if (e.key === "s" || e.key === "S") toggleMode("skip");
    else if (DEBUG && (e.key === "j" || e.key === "J")) {
      const label = prompt("jump to label:\n" + Object.keys(STORY.labels).join(", "));
      if (label && label in STORY.labels) { st.cur = STORY.labels[label]; restore(st); }
    }
  });
  $("#quick").addEventListener("click", (e) => {
    const act = e.target.dataset.act;
    if (act === "hearts") $("#hearts").classList.toggle("hidden");
    if (act === "log") openLog();
    if (act === "auto" || act === "skip") toggleMode(act);
    if (act === "save") openSlots("save");
    if (act === "load") openSlots("load");
    if (act === "menu") openMenu();
  });
  $$(".overlay .close").forEach((b) => b.addEventListener("click", () => { closeAll(); saveOpts(); }));
  $("#to-title").addEventListener("click", () => { saveOpts(); toTitle(); });
  $$("#menu input").forEach((i) => i.addEventListener("input", saveOpts));

  $(".title-inner nav").addEventListener("click", (e) => {
    const act = e.target.dataset.title;
    if (act === "new") {
      st = newState();
      $("#title").classList.add("hidden");
      $("#hud").classList.remove("hidden");
      renderHearts();
      st.pc = STORY.labels.prologue ?? 0;
      st.cur = st.pc;
      run();
    } else if (act === "continue") {
      const a = safeGet("coa_auto", null);
      if (a) restore(a.state);
    } else if (act === "load") {
      st = st || newState();
      openSlots("load");
    } else if (act === "endings") openEndings();
    else if (act === "menu") openMenu();
  });
  window.addEventListener("beforeunload", () => { if (st && $("#title").classList.contains("hidden")) autosave(); });
  setInterval(() => { if (st && $("#title").classList.contains("hidden")) autosave(); }, 15000);
}

// ------------------------------------------------------------------ 부팅
async function boot() {
  bind();
  titleSparks();
  playBgm(TITLE_BGM);
  resumeBgmOnInput();
  try {
    STORY = await (await fetch("data/story.json", { cache: "no-store" })).json();
  } catch {
    $("#server-status").textContent = "data/story.json을 불러오지 못했습니다. server/app.py로 실행하세요.";
    return;
  }
  $('[data-title="continue"]').disabled = !safeGet("coa_auto", null);
  try { MANIFEST = new Set(await (await fetch("data/assets.json", { cache: "no-store" })).json()); } catch { MANIFEST = null; }
  if (DEBUG) $("#hearts").classList.remove("hidden");
  checkServer(API_BASE ? 12 : 1);
}
// 원격 Space는 잠들어 있으면 깨어나는 데 1분 정도 걸리므로 몇 번 다시 확인한다
async function checkServer(tries) {
  for (let i = 1; i <= tries; i++) {
    try {
      const h = await (await fetch(api("api/health"), { cache: "no-store" })).json();
      $("#server-status").textContent = h.model ? `판정 엔진: Laya · ${h.model}` : "판정 엔진: 휴리스틱";
      return;
    } catch {
      if (i < tries) {
        $("#server-status").textContent = `판정 서버 깨우는 중… (${i}/${tries})`;
        await sleep(10000);
      }
    }
  }
  $("#server-status").textContent = "판정 서버 없음 — 오프라인 간이 판정으로 진행합니다";
}
boot();
