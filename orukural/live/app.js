// Studio Live: polls /api/state and redraws when something changed.
"use strict";

const $ = (id) => document.getElementById(id);
const POLL_MS = 2000;
const LIMITS = { clips: 240, images: 120 };   // seconds before the Flow session counts a job as stalled
const KIND = {
  start: ["Started", "c-running"], done: ["Done", "c-done"], fail: ["Failed", "c-failed"],
  retry: ["Retry", "c-running"], wait: ["Waiting", "c-waiting"], blocked: ["Needs you", "c-failed"],
  info: ["Note", "c-waiting"],
};
const STATE = {
  done: "Done", running: "Running", failed: "Failed", waiting: "Waiting", partial: "In progress", todo: "Not yet",
};
const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

let current = null, lastKey = "", data = null, ok = false, lastOk = 0;
const media = new Map();   // keep <img>/<video> nodes between redraws so clips do not restart

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : String(kid));
  return el;
}

function mediaEl(slot, src, kind, opts = {}) {
  const key = slot + "|" + src;
  if (media.has(key)) return media.get(key);
  const el = kind === "video"
    ? h("video", { src, muted: true, loop: true, playsinline: true, preload: "metadata", autoplay: opts.autoplay })
    : h("img", { src, alt: opts.alt || "", loading: "lazy" });
  if (kind === "video") el.muted = true;
  media.set(key, el);
  return el;
}

const hhmm = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
function dur(sec) {
  sec = Math.max(0, Math.round(sec));
  if (sec < 60) return `${sec} s`;
  const m = Math.floor(sec / 60), s = sec % 60;
  if (m < 60) return `${m}:${String(s).padStart(2, "0")}`;
  return `${Math.floor(m / 60)} h ${m % 60} m`;
}

async function poll() {
  const q = new URLSearchParams();
  if (current) q.set("ep", current);
  if ($("dry").checked) q.set("dry", "1");
  try {
    const r = await fetch("/api/state?" + q, { cache: "no-store" });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.status);
    data = j; ok = true; lastOk = Date.now();
    const key = JSON.stringify({ ...j, generated_at: 0, episode: j.episode && { ...j.episode, now: { ...j.episode.now, seconds: 0 } } });
    if (key !== lastKey) { lastKey = key; render(j); }
  } catch (e) {
    ok = false;
    $("updated").textContent = String(e.message || e);
  }
  tick();
}

function render(s) {
  const ep = s.episode;
  const sel = $("episode");
  sel.replaceChildren(...s.episodes.map((e) => h("option", { value: e.id, selected: ep && e.id === ep.id }, `${e.id} ${e.title ? "· " + e.title : ""}`)));
  if (!ep) {
    $("title").textContent = "No episodes yet";
    return;
  }
  current = ep.id;
  $("title").replaceChildren(`${ep.id} · `, h("span", { class: "ta" }, ep.title_ta || ep.title_en));
  document.title = `${ep.now.state === "running" ? "● " : ""}${ep.id} · Studio Live`;
  renderStages(ep);
  renderNow(ep);
  renderBudgets(s.budgets);
  renderShots(ep);
  renderLog(ep);
  renderCal(s);
}

function renderStages(ep) {
  $("stages").replaceChildren(...ep.stages.map((st, i) => h("div", { class: `stage ${st.state}` },
    h("div", null, h("span", { class: "n" }, String(i + 1).padStart(2, "0")), h("span", { class: "name" }, st.label)),
    h("span", { class: "muted small" }, st.total > 1 ? `${st.done} of ${st.total}` : (st.done ? "Done" : "")),
    h("span", { class: `state c-${st.state}` }, STATE[st.state]),
    st.note ? h("span", { class: "muted small" }, st.note) : null)));
}

function renderNow(ep) {
  const n = ep.now;
  const box = $("now-media");
  box.className = "now-media" + (n.state === "running" ? " running" : "");
  box.replaceChildren(n.media ? mediaEl("now", n.media, n.media_kind, { autoplay: true })
    : h("span", null, n.shot ? `Shot ${n.shot} appears here the moment it lands` : "Previews appear here"));
  const v = box.querySelector("video"); if (v) v.play().catch(() => {});
  $("now-eyebrow").textContent = { running: "Happening now", stalled: "No word for a while", idle: "Last step" }[n.state];
  $("now-title").textContent = n.title || "";
  $("now-sub").textContent = [n.stage && ep.stages.find((x) => x.key === n.stage)?.label,
    n.shot && `shot ${n.shot}`, n.attempt && `attempt ${n.attempt}`, n.credits && `${n.credits} credits`].filter(Boolean).join(" · ");
  const done = ep.stages.filter((x) => x.key === "clips")[0];
  $("tiles").replaceChildren(
    tile("Clips done", done ? `${done.done}/${done.total}` : "-"),
    tile("Retries", ep.retries),
    tile("Credits used", ep.credits_spent),
    tile("Running for", ep.started_at ? dur((Date.now() - new Date(ep.started_at)) / 1000) : "-"));
  $("alerts").replaceChildren(...ep.needs_you.map((e) => h("div", { class: "alert" },
    h("strong", null, "Needs you: " + (e.detail || e.stage)),
    h("span", { class: "small muted" }, `${hhmm(e.ts)} · ${e.stage}${e.shot ? " · shot " + e.shot : ""}. The pipeline is paused on this.`))));
  $("draft").replaceChildren(...(ep.draft ? [h("div", { class: "eyebrow" }, "Draft render"),
    h("div", { class: "draft" }, h("video", { src: ep.draft, controls: true, playsinline: true, preload: "metadata" }))] : []));
}

const tile = (label, value) => h("div", { class: "tile" }, h("span", { class: "small muted" }, label), h("b", null, String(value)));

function renderBudgets(b) {
  const f = b.flow;
  const left = f.reported_left != null ? f.reported_left : f.daily_left;
  $("flow").replaceChildren(
    h("div", { class: "eyebrow" }, "Flow credits"),
    h("div", null, h("span", { class: "big" }, left), " ", h("span", { class: "muted" },
      f.reported_left != null ? `left, as Flow showed at ${hhmm(f.reported_at)}` : `of ${f.daily} left today (estimate)`)),
    h("div", { class: "line" }, h("span", null, "Daily"), h("span", { class: "mono" }, `${f.daily_left} / ${f.daily}`)),
    h("div", { class: "meter" }, h("div", { style: `width:${(100 * f.daily_left) / f.daily}%` })),
    h("div", { class: "small muted" }, `Spent today: ${f.spent_today}. Daily credits do not carry over; ${f.monthly} monthly credits are the reserve.`));
  const t = b.tts;
  $("tts").replaceChildren(
    h("div", { class: "eyebrow" }, "Voice (Gemini free tier)"),
    h("div", null, h("span", { class: "big" }, t.left), " ", h("span", { class: "muted" }, `of ${t.limit} requests left today`)),
    h("div", { class: "blocks", style: `grid-template-columns:repeat(${t.limit},1fr)`, role: "img", "aria-label": `${t.used} of ${t.limit} used` },
      ...Array.from({ length: t.limit }, (_, i) => h("span", { class: i < t.used ? "used" : "" }))),
    h("div", { class: "small", id: "tts-reset", "data-at": t.resets_at }));
  $("spend").replaceChildren(
    h("div", null, h("div", { class: "small muted" }, "Paid API spend, all episodes"), h("span", { class: "big" }, "$" + b.spend_usd_total.toFixed(2))),
    h("span", { class: "small c-done" }, b.spend_usd_total ? "" : "Zero-spend mode"));
}

function verdictText(v, has, label) {
  if (v === "pass") return h("b", { class: "c-done" }, "pass");
  if (v) return h("b", { class: "c-failed" }, "redo");
  return h("b", { class: has ? "c-waiting" : "c-todo" }, has ? "to check" : label);
}

function renderShots(ep) {
  $("shots").replaceChildren(...ep.shots.map((sh) => {
    const cls = ["shot", sh.running && "running", sh.clip_verdict === "pass" && "clip-done",
      (sh.image_verdict && sh.image_verdict !== "pass") || (sh.clip_verdict && sh.clip_verdict !== "pass") ? "has-fail" : ""].filter(Boolean).join(" ");
    const frame = h("div", { class: "frame" }, h("span", { class: "num" }, sh.n));
    if (sh.image) frame.append(mediaEl("card", sh.image, "image", { alt: `Shot ${sh.n}` }));
    else frame.append(h("span", { class: "cap" }, sh.caption));
    let vid = null;
    if (sh.clip) { vid = mediaEl("card", sh.clip, "video"); vid.style.opacity = sh.image ? 0 : 1; frame.append(vid); }
    const btn = h("button", { type: "button", class: cls, "aria-label": `Shot ${sh.n} details`, onclick: () => openShot(sh) },
      frame,
      h("span", { class: "meta" }, "Image ", verdictText(sh.image_verdict, !!sh.image, "waiting")),
      h("span", { class: "meta" }, "Clip ", sh.animated ? verdictText(sh.clip_verdict, !!sh.clip, sh.running ? "making" : "waiting") : "none"),
      sh.tries || sh.credits ? h("span", { class: "meta" }, [sh.tries && `${sh.tries} ${sh.tries === 1 ? "retry" : "retries"}`, sh.credits && `${sh.credits} cr`].filter(Boolean).join(" · ")) : null);
    if (vid && sh.image) {
      btn.addEventListener("mouseenter", () => { vid.style.opacity = 1; vid.play().catch(() => {}); });
      btn.addEventListener("mouseleave", () => { vid.pause(); vid.style.opacity = 0; });
    }
    return btn;
  }));
}

function openShot(sh) {
  const pair = h("div", { class: "pair" },
    h("div", null, sh.image ? h("img", { src: sh.image, alt: `Shot ${sh.n} image` }) : "No image yet"),
    h("div", null, sh.clip ? h("video", { src: sh.clip, controls: true, autoplay: true, muted: true, loop: true, playsinline: true }) : "No clip yet"));
  $("shot-detail").replaceChildren(h("div", { class: "detail" }, pair, h("div", { class: "info" },
    h("h2", null, `Shot ${sh.n} · ${sh.beat}`),
    h("div", { class: "small" }, "Image check: ", sh.image_verdict || "not reviewed"),
    h("div", { class: "small" }, "Clip check: ", sh.clip_verdict || "not reviewed"),
    h("pre", null, sh.prompt),
    sh.events.length ? h("div", null, ...sh.events.slice().reverse().map(evRow)) : h("div", { class: "small muted" }, "No logged tries yet."))));
  $("shot-dialog").showModal();
}

function evRow(e) {
  const [label, cls] = KIND[e.status] || [e.status, "c-waiting"];
  const extra = [e.shot && `shot ${e.shot}`, e.attempt && `attempt ${e.attempt}`, e.credits && `${e.credits} credits`,
    e.seconds && dur(e.seconds)].filter(Boolean).join(" · ");
  return h("div", { class: "ev" }, h("span", { class: "t" }, hhmm(e.ts)), h("span", { class: `k ${cls}` }, label),
    h("div", null, h("div", { class: "w" }, e.detail || e.stage), h("div", { class: "d" }, [e.stage, extra].filter(Boolean).join(" · "))));
}

function renderLog(ep) {
  $("log").replaceChildren(...(ep.events.length ? ep.events.map(evRow)
    : [h("div", { class: "muted small" }, "Nothing logged yet. Steps show up here as they run.")]));
}

function renderCal(s) {
  $("cal").replaceChildren(h("div", { class: "small muted", style: "margin-bottom:10px" }, `Posts go out at ${s.post_time}`),
    ...s.calendar.map((d) => {
      const date = new Date(d.date + "T12:00:00");
      const title = d.kind === "weekly_run" ? "Weekly run" : (d.episode_id ? `${d.episode_id} · ${d.theme}` : "Nothing planned");
      const status = d.kind === "weekly_run" ? "Scripts for the week" : (d.status || "");
      return h("div", { class: "day" }, h("div", { class: "date" }, h("span", { class: "small muted" }, DOW[date.getDay()]), h("b", null, date.getDate())),
        h("div", null, h("div", null, title), h("div", { class: "small " + (d.episode_id === current ? "c-running" : "muted") }, status)));
    }));
}

// Every second: clocks and countdowns, without a redraw.
function tick() {
  const live = $("live");
  const fresh = ok && Date.now() - lastOk < 10000;
  live.className = "pill " + (fresh ? "ok" : "off");
  live.textContent = fresh ? "Live" : "Disconnected";
  if (fresh) $("updated").textContent = `updated ${dur((Date.now() - lastOk) / 1000)} ago`;
  const n = data && data.episode && data.episode.now;
  if (n && n.since) {
    const sec = (Date.now() - new Date(n.since)) / 1000;
    const limit = n.state === "running" ? LIMITS[n.stage] : null;
    $("now-elapsed").textContent = n.state === "running" ? `${dur(sec)} so far` : `${dur(sec)} ago`;
    $("now-limit").textContent = limit ? `counts as stalled at ${dur(limit)}` : "";
    $("now-bar").style.width = limit ? Math.min(100, (100 * sec) / limit) + "%" : (n.state === "running" ? "100%" : "0");
  }
  const r = $("tts-reset");
  if (r) r.textContent = `Resets at ${hhmm(r.dataset.at)} (in ${dur((new Date(r.dataset.at) - Date.now()) / 1000)})`;
}

$("episode").addEventListener("change", (e) => { current = e.target.value; lastKey = ""; poll(); });
$("dry").addEventListener("change", () => { lastKey = ""; media.clear(); poll(); });
poll();
setInterval(poll, POLL_MS);
setInterval(tick, 1000);
