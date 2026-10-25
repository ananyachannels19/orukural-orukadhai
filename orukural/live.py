"""Studio Live: a local dashboard that shows every pipeline step as it happens.

`python studio.py live` serves http://127.0.0.1:8765 from this Mac. The page polls
`/api/state` every two seconds; everything it shows is read from disk:

  episodes/<id>/script.json, voice/, refs/, images/, clips/, render/   what exists
  episodes/<id>/continuity_review.json                                 pass / reason per shot
  episodes/<id>/flow/jobs.json                                         refs, clip days, credits
  logs/spend.jsonl                                                     paid calls, TTS requests
  logs/events.jsonl                                                    what happened, as it happened

Only `logs/events.jsonl` is new. Pipeline steps (and the Flow session on the Mac, through
`studio.py event`) append one line per thing that happens with `emit()`. Writing an event
never raises: a broken log must never stop a render.
"""

from __future__ import annotations

import datetime as dt
import json
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .config import Settings

STAGES = (
    ("script", "Script"),
    ("voice", "Voice"),
    ("refs", "References"),
    ("images", "Shot images"),
    ("image_check", "Image check"),
    ("clips", "Clips"),
    ("clip_check", "Clip check"),
    ("render", "Render"),
    ("review", "Your review"),
    ("publish", "Publish"),
)
STATUSES = ("start", "done", "fail", "retry", "wait", "blocked", "info")
EVENTS_FILE = "logs/events.jsonl"
MEDIA_DIRS = ("episodes", "review", "assets")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
RUNNING_FOR = 15 * 60   # a "start" with nothing after it for this long is shown as stalled
_lock = threading.Lock()


def _now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def _tz(name: str):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:  # no tz database: fall back to the machine's own zone
        return _now().tzinfo


# ---- writing events -----------------------------------------------------------------

def emit(s: Settings, episode_id: str, stage: str, status: str, detail: str = "", **fields) -> dict | None:
    """Append one event to logs/events.jsonl. Useful fields: shot, attempt, credits
    (Flow credits this step spent), credits_left (what Flow shows), requests (TTS calls), seconds."""
    try:
        event = {"ts": _now().isoformat(timespec="seconds"), "episode_id": episode_id,
                 "stage": stage, "status": status, "detail": detail,
                 **{k: v for k, v in fields.items() if v is not None}}
        path = s.root / EVENTS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with _lock, path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event
    except Exception:
        return None


def read_events(s: Settings, episode_id: str | None = None) -> list[dict]:
    path = s.root / EVENTS_FILE
    if not path.exists():
        return []
    out = []
    for line in path.read_text("utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue  # a half-written last line while a step is appending
        if episode_id is None or e.get("episode_id") == episode_id:
            out.append(e)
    return out


# ---- reading the episode from disk ----------------------------------------------------

def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _find(stem: Path, exts: tuple[str, ...]) -> Path | None:
    for ext in exts:
        if stem.with_suffix(ext).exists():
            return stem.with_suffix(ext)
    return None


def _ts(e: dict) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(e["ts"])
    except (KeyError, ValueError):
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)


def episodes(s: Settings) -> list[dict]:
    root = s.path("episodes")
    eps = [d for d in root.glob("K*") if (d / "script.json").exists()] if root.exists() else []
    eps.sort(key=lambda d: max((p.stat().st_mtime for p in d.rglob("*") if p.is_file()), default=0), reverse=True)
    return [{"id": d.name, "title": _json(d / "script.json").get("script", {}).get("story_title_en", "")} for d in eps]


class _Episode:
    def __init__(self, s: Settings, episode_id: str, dry_run: bool = False):
        self.s, self.id = s, episode_id
        base = s.path("episodes") / episode_id
        self.dir = base / "dryrun" if dry_run else base
        payload = _json(base / "script.json")
        self.errors = payload.get("errors") or []
        self.script = payload.get("script", {})
        self.shots = self.script.get("shots", [])
        self.segments = self.script.get("segments", [])
        self.review = _json(self.dir / "continuity_review.json")
        self.jobs = _json(self.dir / "flow" / "jobs.json")
        self.events = read_events(s, episode_id)

    def url(self, p: Path | None) -> str | None:
        if not p or not p.exists():
            return None
        return f"/media/{p.relative_to(self.s.root).as_posix()}?v={int(p.stat().st_mtime)}"

    def verdict(self, kind: str, n: int) -> str:
        return str(self.review.get(kind, {}).get(str(n), "")).strip()

    def animated(self) -> set[int]:
        nums = {int(sh["n"]) for sh in self.shots}
        if self.s["video"].get("animate", "all") == "all":
            return nums
        planned = {j["shot"] for j in self.jobs.get("jobs", []) if j.get("kind") == "clip"}
        made = {n for n in nums if (self.dir / "clips" / f"shot{n:02d}.mp4").exists()}
        return planned | made


def _stage_state(ep: _Episode, key: str, done: int, total: int) -> dict:
    evs = [e for e in ep.events if e.get("stage") == key and e.get("status") != "info"]
    last = evs[-1] if evs else None
    if total and done >= total:
        state = "done"
    elif last and last["status"] in ("start", "retry") and (_now() - _ts(last)).total_seconds() < RUNNING_FOR:
        state = "running"
    elif last and last["status"] in ("fail", "blocked"):
        state = "failed"
    elif last and last["status"] == "wait":
        state = "waiting"
    elif done:
        state = "partial"
    else:
        state = "todo"
    return {"key": key, "state": state, "done": done, "total": total,
            "note": (last or {}).get("detail", "") if state in ("running", "failed", "waiting") else ""}


def _stages(ep: _Episode, kural: dict) -> list[dict]:
    shots = [int(sh["n"]) for sh in ep.shots]
    anim = sorted(ep.animated())
    segs = len(ep.segments)
    voiced = sum(1 for i, seg in enumerate(ep.segments)
                 if (ep.dir / "voice" / f"seg{i + 1:02d}_{seg.get('beat', '')}.mp3").exists())
    refs = [j for j in ep.jobs.get("jobs", []) if str(j.get("kind", "")).endswith("_ref")]
    refs_made = sum(1 for j in refs if (ep.s.root / j["save_as"]).exists())
    images = sum(1 for n in shots if _find(ep.dir / "images" / f"shot{n:02d}", IMAGE_EXT))
    img_ok = sum(1 for n in shots if ep.verdict("images", n) == "pass")
    clips = sum(1 for n in anim if (ep.dir / "clips" / f"shot{n:02d}.mp4").exists())
    clip_ok = sum(1 for n in anim if ep.verdict("clips", n) == "pass")
    rendered = int((ep.dir / "render" / f"{ep.id}_draft.mp4").exists())
    status = kural.get("status", "planned")
    order = ("planned", "scripted", "rendered", "approved", "scheduled", "posted")
    rank = order.index(status) if status in order else 0
    counts = {
        "script": (0 if ep.errors or not ep.script else 1, 1),
        "voice": (voiced, segs),
        "refs": (refs_made, len(refs)),
        "images": (images, len(shots)),
        "image_check": (img_ok, len(shots)),
        "clips": (clips, len(anim)),
        "clip_check": (clip_ok, len(anim)),
        "render": (rendered, 1),
        "review": (int(rank >= 3), 1),
        "publish": (int(rank >= 5), 1),
    }
    out = []
    for key, label in STAGES:
        st = _stage_state(ep, key, *counts[key])
        st["label"] = label
        if key == "script" and ep.errors:
            st["state"], st["note"] = "failed", ep.errors[0]
        out.append(st)
    return out


def _shot_cards(ep: _Episode) -> list[dict]:
    anim = ep.animated()
    cards = []
    for sh in ep.shots:
        n = int(sh["n"])
        image = _find(ep.dir / "images" / f"shot{n:02d}", IMAGE_EXT)
        clip = ep.dir / "clips" / f"shot{n:02d}.mp4"
        evs = [e for e in ep.events if e.get("shot") == n]
        live_evs = [e for e in evs if e.get("status") != "info"]
        words = str(sh.get("image_prompt_en", "")).split()
        cards.append({
            "n": n, "beat": sh.get("beat", ""), "caption": " ".join(words[:9]) + ("…" if len(words) > 9 else ""),
            "prompt": sh.get("image_prompt_en", ""),
            "image": ep.url(image), "clip": ep.url(clip) if n in anim else None, "animated": n in anim,
            "image_verdict": ep.verdict("images", n), "clip_verdict": ep.verdict("clips", n),
            "tries": sum(1 for e in evs if e.get("status") in ("retry", "fail", "blocked")),
            "credits": sum(int(e.get("credits") or 0) for e in evs),
            "running": bool(live_evs) and live_evs[-1].get("status") in ("start", "retry")
                       and (_now() - _ts(live_evs[-1])).total_seconds() < RUNNING_FOR,
            "events": evs[-6:],
        })
    return cards


def _now_card(ep: _Episode, cards: list[dict]) -> dict:
    evs = [e for e in ep.events if e.get("status") != "info"] or ep.events  # a note never hides a running step
    if not evs:
        return {"state": "idle", "title": "Nothing logged yet", "detail": "Steps appear here as soon as they start."}
    last = evs[-1]
    age = (_now() - _ts(last)).total_seconds()
    running = last["status"] in ("start", "retry") and age < RUNNING_FOR
    shot = next((c for c in cards if c["n"] == last.get("shot")), None)
    return {
        "state": "running" if running else ("stalled" if last["status"] in ("start", "retry") else "idle"),
        "stage": last.get("stage"), "status": last["status"], "title": last.get("detail") or last.get("stage"),
        "since": last["ts"], "seconds": int(age), "attempt": last.get("attempt"), "credits": last.get("credits"),
        "shot": shot["n"] if shot else None,
        "media": (shot["clip"] or shot["image"]) if shot else None,
        "media_kind": ("video" if shot["clip"] else "image") if shot and (shot["clip"] or shot["image"]) else None,
    }


def _needs_you(ep: _Episode) -> list[dict]:
    """Blocked events that nothing has happened after, for the same stage (and shot)."""
    out = []
    for i, e in enumerate(ep.events):
        if e.get("status") != "blocked":
            continue
        later = ep.events[i + 1:]
        if not any(x.get("stage") == e.get("stage") and x.get("shot") == e.get("shot") and x.get("status") not in ("blocked", "info")
                   for x in later):
            out.append(e)
    return out[-3:]


def _budgets(s: Settings) -> dict:
    events = read_events(s)
    now = _now()
    # Flow: Google AI Plus daily credits (lost at reset) plus a monthly pool.
    daily, monthly = s["flow"]["daily_credits"], s["flow"]["monthly_credits"]
    spent_today = sum(int(e.get("credits") or 0) for e in events if _ts(e).astimezone(now.tzinfo).date() == now.date())
    flow_seen = [e for e in events if e.get("credits_left") is not None]
    flow = {"daily": daily, "monthly": monthly, "spent_today": spent_today,
            "daily_left": max(0, daily - spent_today),
            "reported_left": flow_seen[-1]["credits_left"] if flow_seen else None,
            "reported_at": flow_seen[-1]["ts"] if flow_seen else None}
    # Gemini free TTS: requests per day, reset at midnight Pacific time.
    pt = _tz("America/Los_Angeles")
    today_pt = now.astimezone(pt).date()
    ledger = s.path("ledger")
    calls = 0
    if ledger.exists():
        for line in ledger.read_text("utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("step") == "voice" and _ts(e).astimezone(pt).date() == today_pt:
                calls += 1
    calls += sum(int(e.get("requests") or 0) for e in events if _ts(e).astimezone(pt).date() == today_pt)
    limit = int(s.raw.get("live", {}).get("tts_requests_per_day", 10))
    reset = dt.datetime.combine(today_pt + dt.timedelta(days=1), dt.time(0), tzinfo=pt).astimezone(now.tzinfo)
    tts = {"limit": limit, "used": min(calls, limit), "left": max(0, limit - calls), "resets_at": reset.isoformat()}
    # Money: the paid-call ledger.
    spend = 0.0
    if ledger.exists():
        for line in ledger.read_text("utf-8").splitlines():
            try:
                spend += float(json.loads(line).get("cost_usd", 0))
            except (ValueError, TypeError):
                continue
    return {"flow": flow, "tts": tts, "spend_usd_total": round(spend, 4)}


def _calendar(s: Settings, store, current: str | None, days: int = 14) -> list[dict]:
    sched = s["schedule"]
    tz = _tz(sched.get("timezone", "Asia/Kolkata"))
    today = _now().astimezone(tz).date()
    names = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    post_days = {names.index(d) for d in sched.get("post_days", [])}
    job_day = names.index(sched["weekly_job_day"]) if sched.get("weekly_job_day") in names else None
    queue = [k for k in store.items if k.get("status") in ("scripted", "rendered", "approved", "scheduled")]
    queue.sort(key=lambda k: (k["id"] != current, k["number"]))
    queue += store.next_planned(s["adhikaram_order"], 6)
    out = []
    for i in range(days):
        d = today + dt.timedelta(days=i)
        if d.weekday() in post_days:
            k = queue.pop(0) if queue else None
            out.append({"date": d.isoformat(), "kind": "post", "time": sched.get("post_time"),
                        "episode_id": k["id"] if k else None, "theme": (k or {}).get("theme", ""),
                        "status": (k or {}).get("status", "")})
        elif d.weekday() == job_day:
            out.append({"date": d.isoformat(), "kind": "weekly_run"})
    return out


def state(s: Settings, episode_id: str | None = None, dry_run: bool = False) -> dict:
    from .kurals import KuralStore
    eps = episodes(s)
    episode_id = episode_id or (eps[0]["id"] if eps else None)
    store = KuralStore(s.path("kurals"))
    out = {"generated_at": _now().isoformat(timespec="seconds"), "episodes": eps, "episode": None,
           "budgets": _budgets(s), "calendar": _calendar(s, store, episode_id),
           "post_time": s["schedule"].get("post_time"), "dry_run": dry_run}
    if not episode_id:
        return out
    ep = _Episode(s, episode_id, dry_run)
    try:
        kural = store.get(episode_id)
    except KeyError:
        kural = {}
    cards = _shot_cards(ep)
    started = [e for e in ep.events if e.get("status") == "start"]
    draft = ep.dir / "render" / f"{episode_id}_draft.mp4"
    out["episode"] = {
        "id": episode_id, "status": kural.get("status"), "number": kural.get("number"),
        "title_ta": ep.script.get("story_title_ta", ""), "title_en": ep.script.get("story_title_en", ""),
        "adhikaram": kural.get("adhikaram", {}).get("name_en", ""),
        "stages": _stages(ep, kural), "shots": cards, "now": _now_card(ep, cards),
        "needs_you": _needs_you(ep),
        "events": list(reversed(ep.events[-40:])),
        "started_at": started[0]["ts"] if started else None,
        "retries": sum(1 for e in ep.events if e.get("status") in ("retry", "fail", "blocked")),
        "credits_spent": sum(int(e.get("credits") or 0) for e in ep.events),
        "draft": ep.url(draft),
        "notes_md": (ep.dir / "flow" / "notes.md").read_text("utf-8")[-4000:]
                    if (ep.dir / "flow" / "notes.md").exists() else "",
    }
    return out


# ---- the server -----------------------------------------------------------------------

STATIC = Path(__file__).with_name("live")


def make_handler(s: Settings):
    roots = [(s.root / d).resolve() for d in MEDIA_DIRS]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet: the dashboard polls every 2 s
            pass

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            url = urlparse(self.path)
            q = parse_qs(url.query)
            try:
                if url.path in ("/", "/index.html"):
                    return self._static("index.html")
                if url.path in ("/app.js", "/app.css"):
                    return self._static(url.path[1:])
                if url.path == "/api/state":
                    body = json.dumps(state(s, (q.get("ep") or [None])[0], (q.get("dry") or ["0"])[0] == "1"),
                                      ensure_ascii=False).encode("utf-8")
                    return self._send(200, body, "application/json; charset=utf-8")
                if url.path.startswith("/media/"):
                    return self._media(unquote(url.path[len("/media/"):]))
            except Exception as exc:  # show the error on the page instead of a dead socket
                return self._send(500, json.dumps({"error": str(exc)}).encode(), "application/json")
            self._send(404, b"not found", "text/plain")

        def _static(self, name: str):
            p = STATIC / name
            self._send(200, p.read_bytes(), mimetypes.guess_type(p.name)[0] or "text/plain")

        def _media(self, rel: str):
            p = (s.root / rel).resolve()
            if not p.is_file() or not any(p.is_relative_to(r) for r in roots):
                return self._send(404, b"not found", "text/plain")
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            size = p.stat().st_size
            rng = self.headers.get("Range")
            if rng and rng.startswith("bytes="):  # Safari will not play a video without ranges
                start_s, _, end_s = rng[6:].partition("-")
                start = int(start_s or 0)
                end = min(int(end_s) if end_s else size - 1, size - 1)
                with p.open("rb") as f:
                    f.seek(start)
                    body = f.read(end - start + 1)
                return self._send(206, body, ctype, {"Content-Range": f"bytes {start}-{end}/{size}",
                                                     "Accept-Ranges": "bytes"})
            self._send(200, p.read_bytes(), ctype, {"Accept-Ranges": "bytes"})

    return Handler


def serve(s: Settings, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(s))
    url = f"http://{'localhost' if host in ('127.0.0.1', '0.0.0.0') else host}:{port}/"
    print(f"Studio Live on {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
