"use strict";
const data = JSON.parse(document.getElementById("evidence-data").textContent);
const messages = {
  zh: {
    subtitle: "逐帧查看准备、触球、随挥和回收，结合连续画面对照动作。",
    sourcePreserved: "原视频与音轨保持原文件",
    readReport: "完整分析报告",
    seeEvidence: "连续帧对比",
    print: "打印报告",
    contents: "报告目录",
    markdown: "打开 Markdown 原稿",
    comparisonNote:
      "左右是不同动作的对照，各自窗口内部按实际帧时间推进。以估计触球时间对齐；毫秒用于定位帧，不表示触球判断精确到毫秒。",
    left: "左侧动作 · 控制时间轴",
    right: "右侧动作 · 按触球附近对齐",
    enlarge: "放大这一帧",
    sheet: "整段动作图",
    seek: "在原视频看这段",
    prev: "← 上一帧",
    next: "下一帧 →",
    play: "慢速连续回看",
    pause: "暂停",
    prepare: "准备附近",
    contact: "触球附近",
    follow: "随挥附近",
    recover: "回收附近",
    swap: "交换左右",
    timeline: "左侧原始帧时间轴",
    keys: "左右方向键逐帧，空格慢速回看。裁切宽度可能不同，画面中人物大小不能用来比较速度。相邻截图没有补帧；JPEG 截图只是预览，不改变原视频。",
    original: "原视频 · 原声回看",
    audioNote:
      "此播放器直接读取原视频。逐帧图片没有声音；视频保留原文件的画质、帧率和音轨。",
    openVideo: "在本机播放器打开原视频",
    videoError: "浏览器无法播放此视频，请在本机播放器按上方时间定位。",
    imageError: "有图片未能加载。请保持 HTML 与证据文件夹的相对位置。",
    footer: "本地报告，无遥测；技术建议需结合实际来球和落点验证。",
    windows: "组连续窗口",
    frames: "张实际帧",
    checked: "窗口已核对剪辑边界",
    unchecked: "剪辑边界尚未核对",
    frame: "窗口帧",
    timelineTime: "成片时间",
    boundary: "已到该窗口边界",
    relative: "相对估计触球",
    unconfirmed: "触球未确认，按窗口中点定位动作",
    missingObservation: "尚未填写视觉观察；截图工具不会自动判断技术问题。",
  },
  en: {
    subtitle:
      "Compare preparation, contact, follow-through and recovery in consecutive frames.",
    sourcePreserved: "Source video and audio remain unchanged",
    readReport: "Read full review",
    seeEvidence: "Continuous frame comparison",
    print: "Print report",
    contents: "Contents",
    markdown: "Open Markdown source",
    comparisonNote:
      "The panels compare different actions. Each window advances through its actual frames. Alignment uses estimated contact; millisecond labels locate frames, not millisecond-accurate impact measurements.",
    left: "Left action · controls the timeline",
    right: "Right action · aligned near contact",
    enlarge: "Open full-size frame",
    sheet: "Sequence sheet",
    seek: "Review in source video",
    prev: "← Previous frame",
    next: "Next frame →",
    play: "Slow playback",
    pause: "Pause",
    prepare: "Preparation",
    contact: "Near contact",
    follow: "Follow-through",
    recover: "Recovery",
    swap: "Swap panels",
    timeline: "Left frame timeline",
    keys: "Arrow keys step frames; Space toggles slow playback. Crops may differ: subject size is not a speed measurement. Frames are not interpolated. JPEG previews do not alter the source video.",
    original: "Source video · original audio",
    audioNote:
      "This player reads the source file directly. Still frames have no sound; video retains its source quality, frame rate and audio.",
    openVideo: "Open original video",
    videoError:
      "This browser cannot play the video. Open the source in a local player and seek to the displayed time.",
    imageError:
      "An image failed to load. Keep the HTML and evidence directories in their relative locations.",
    footer:
      "Local report, no telemetry. Validate coaching suggestions against actual balls and landing positions.",
    windows: "continuous windows",
    frames: "actual frames",
    checked: "Windows checked against cut boundaries",
    unchecked: "Cut boundaries have not been checked",
    frame: "window frame",
    timelineTime: "Video time",
    boundary: "at window boundary",
    relative: "Relative to estimated contact",
    unconfirmed: "Contact unconfirmed; action positioned at window midpoint",
    missingObservation:
      "Visual observation not entered. The extraction tools do not diagnose technique.",
  },
};
const text = messages[data.language] || messages.en;
const $ = (id) => document.getElementById(id);
document.querySelectorAll("[data-i18n]").forEach((el) => {
  el.textContent = text[el.dataset.i18n] || el.dataset.i18n;
});
if (!$("intro").textContent.trim()) $("intro").textContent = text.subtitle;
document.querySelectorAll('a[href="#report"]').forEach((link) => {
  link.addEventListener("click", () => {
    $("report").open = true;
  });
});
$("scope").textContent =
  `${data.validation.window_count} ${text.windows} · ${data.validation.frame_count} ${text.frames}`;
$("continuity").textContent =
  data.validation.cut_check === "checked" ? text.checked : text.unchecked;
const records = Object.fromEntries(data.windows.map((w) => [w.id, w]));
let index = 0,
  timer = null;
function stamp(t) {
  const ms = Math.round(t * 1000),
    minutes = Math.floor(ms / 60000),
    seconds = Math.floor((ms % 60000) / 1000);
  return (
    String(minutes).padStart(2, "0") +
    ":" +
    String(seconds).padStart(2, "0") +
    "." +
    String(ms % 1000).padStart(3, "0")
  );
}
function anchor(w) {
  return w.contact_time === null || w.contact_time === undefined
    ? (w.start + w.end) / 2
    : w.contact_time;
}
function nearest(frames, t) {
  let low = 0,
    high = frames.length - 1;
  while (low < high) {
    const mid = (low + high) >> 1;
    if (frames[mid].time < t) low = mid + 1;
    else high = mid;
  }
  return low > 0 &&
    Math.abs(frames[low - 1].time - t) < Math.abs(frames[low].time - t)
    ? low - 1
    : low;
}
function record(side) {
  return records[$(side + "Select").value];
}
function stop() {
  if (timer !== null) clearTimeout(timer);
  timer = null;
  $("play").textContent = text.play;
}
function show(side, w, i, clamped) {
  const f = w.frames[i];
  $(side + "Img").src = f.src;
  $(side + "Full").href = f.src;
  $(side + "Stamp").textContent =
    `${text.timelineTime} ${stamp(f.time)} · ${text.frame} ${i + 1}/${w.frames.length}${clamped ? " · " + text.boundary : ""}`;
  $(side + "Note").textContent = w.observation || text.missingObservation;
  $(side + "Sheet").hidden = !w.sheet;
  if (w.sheet) $(side + "Sheet").href = w.sheet;
}
function render() {
  const l = record("left"),
    r = record("right");
  index = Math.max(0, Math.min(index, l.frames.length - 1));
  const rel = l.frames[index].time - anchor(l),
    target = anchor(r) + rel,
    ri = nearest(r.frames, target);
  show("left", l, index, false);
  show(
    "right",
    r,
    ri,
    target < r.frames[0].time || target > r.frames.at(-1).time,
  );
  $("timeline").max = l.frames.length - 1;
  $("timeline").value = index;
  $("prev").disabled = index === 0;
  $("next").disabled = index === l.frames.length - 1;
  const unknown = l.contact_time == null || r.contact_time == null;
  const displayRel = Math.abs(rel) < 0.0005 ? 0 : rel;
  $("status").textContent =
    (unknown ? text.unconfirmed : text.relative) +
    `: ${displayRel >= 0 ? "+" : ""}${displayRel.toFixed(3)} s`;
  document.querySelectorAll("[data-offset]").forEach((b) => {
    b.disabled = l.contact_time == null;
  });
}
function advance(n) {
  stop();
  index += n;
  render();
}
for (const side of ["left", "right"]) {
  for (const w of data.windows) {
    const option = document.createElement("option");
    option.value = w.id;
    option.textContent = `${w.id} · ${stamp(anchor(w))} · ${w.kind || ""}`;
    $(side + "Select").append(option);
  }
  $(side + "Select").addEventListener("change", () => {
    stop();
    if (side === "left") {
      const w = record(side);
      index = nearest(w.frames, anchor(w));
    }
    render();
  });
  $(side + "Img").addEventListener("error", () => {
    $("imageError").hidden = false;
  });
}
const defaults = data.default_comparison || [];
$("leftSelect").value = records[defaults[0]] ? defaults[0] : data.windows[0].id;
$("rightSelect").value = records[defaults[1]]
  ? defaults[1]
  : data.windows[Math.min(1, data.windows.length - 1)].id;
index = nearest(record("left").frames, anchor(record("left")));
function tick() {
  const w = record("left");
  if (index >= w.frames.length - 1) {
    stop();
    return;
  }
  const delay = Math.max(
    10,
    (w.frames[index + 1].time - w.frames[index].time) * 4000,
  );
  timer = setTimeout(() => {
    index++;
    render();
    tick();
  }, delay);
}
$("prev").addEventListener("click", () => advance(-1));
$("next").addEventListener("click", () => advance(1));
$("play").addEventListener("click", () => {
  if (timer !== null) {
    stop();
    return;
  }
  if (index >= record("left").frames.length - 1) index = 0;
  render();
  $("play").textContent = text.pause;
  tick();
});
$("timeline").addEventListener("input", () => {
  stop();
  index = Number($("timeline").value);
  render();
});
document.querySelectorAll("[data-offset]").forEach((el) =>
  el.addEventListener("click", () => {
    stop();
    const w = record("left");
    index = nearest(w.frames, anchor(w) + Number(el.dataset.offset));
    render();
  }),
);
$("swap").addEventListener("click", () => {
  stop();
  const l = record("left"),
    rel = l.frames[index].time - anchor(l),
    old = $("leftSelect").value;
  $("leftSelect").value = $("rightSelect").value;
  $("rightSelect").value = old;
  const w = record("left");
  index = nearest(w.frames, anchor(w) + rel);
  render();
});
document.addEventListener("keydown", (e) => {
  if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName))
    return;
  if (e.key === "ArrowLeft") {
    e.preventDefault();
    advance(-1);
  }
  if (e.key === "ArrowRight") {
    e.preventDefault();
    advance(1);
  }
  if (
    e.code === "Space" &&
    !["BUTTON", "SUMMARY", "A", "VIDEO"].includes(
      document.activeElement.tagName,
    )
  ) {
    e.preventDefault();
    $("play").click();
  }
});
$("print").addEventListener("click", () => {
  stop();
  $("report").open = true;
  window.print();
});
const video = $("video"),
  videoURI = video.dataset.source;
if (videoURI) {
  video.src = videoURI;
  $("originalLink").href = videoURI;
} else {
  $("original").hidden = true;
  $("leftVideo").hidden = true;
  $("rightVideo").hidden = true;
}
function seek(w) {
  stop();
  $("original").scrollIntoView({ behavior: "smooth" });
  const t = Math.max(0, anchor(w) - 1.3),
    go = () => {
      video.currentTime = t;
      video.play().catch(() => {});
    };
  if (video.readyState >= 1) go();
  else {
    video.addEventListener("loadedmetadata", go, { once: true });
    video.load();
  }
}
for (const side of ["left", "right"])
  $(side + "Video").addEventListener("click", () => seek(record(side)));
video.addEventListener("error", () => {
  $("videoError").hidden = false;
});
render();
