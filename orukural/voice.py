"""Phase 2: Tamil narration with ElevenLabs, one file per script segment.

Each segment is voiced separately with the text before and after it as context, so the
read stays natural while we keep exact timings per beat. The API's character timings
are saved next to each file for word-level subtitles (phase 3).
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

import requests
import yaml

from . import media
from .config import Settings
from .ledger import Ledger
from .schema import EpisodeScript, tamil_letters

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"


def load_fixes(s: Settings) -> dict[str, str]:
    data = yaml.safe_load(s.file("pronunciation_file").read_text("utf-8")) or {}
    return data.get("fixes") or {}


def spoken_text(text: str, fixes: dict[str, str]) -> str:
    """Apply pronunciation respellings (longest first) and drop on-screen-only symbols."""
    for written in sorted(fixes, key=len, reverse=True):
        text = text.replace(written, fixes[written])
    return re.sub(r"[➜→•]", "", text).strip()


def voice_for(s: Settings, speaker: str) -> str:
    cfg = s["voice"]
    vid = (cfg.get("speaker_voices") or {}).get(speaker) or cfg["voice_id"]
    if not vid:
        raise SystemExit("voice.voice_id is empty in config.yaml")
    return vid


def _tts(s: Settings, voice_id: str, text: str, prev: str, nxt: str, out: Path) -> tuple[dict, float, dict]:
    cfg = s["voice"]
    body = {
        "text": text,
        "model_id": cfg["model"],
        "previous_text": prev or None,
        "next_text": nxt or None,
        "voice_settings": {"stability": cfg["stability"], "similarity_boost": cfg["similarity_boost"]},
        "seed": 1330,
    }
    if cfg.get("language_code") and not cfg["model"].startswith("eleven_multilingual"):
        body["language_code"] = cfg["language_code"]
    r = requests.post(
        API.format(voice_id=voice_id),
        params={"output_format": cfg["output_format"]},
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "content-type": "application/json"},
        json=body,
        timeout=180,
    )
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:500]}")
    data = r.json()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(data["audio_base64"]))
    cost = len(text) / 1000 * cfg["price_per_1k_chars"]
    value = {"file": str(out), "alignment": data.get("alignment"), "normalized_alignment": data.get("normalized_alignment")}
    return value, cost, {"provider": "elevenlabs", "model": cfg["model"], "chars": len(text),
                         "request_id": r.headers.get("request-id")}


def generate(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str, force: bool = False) -> dict:
    """Voice every segment; returns and writes voice/voice.json with real durations."""
    media.require_ffmpeg()
    vdir = ep_dir / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    fixes = load_fixes(s)
    segs = script.segments
    ledger = Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])
    if not s.dry_run and not os.environ.get("ELEVENLABS_API_KEY"):
        raise SystemExit("ELEVENLABS_API_KEY is not set. Add it to .env, or run with --dry-run.")

    items, spent = [], 0.0
    for i, seg in enumerate(segs):
        text = spoken_text(seg.narration_ta, fixes)
        prev = spoken_text(segs[i - 1].narration_ta, fixes) if i else ""
        nxt = spoken_text(segs[i + 1].narration_ta, fixes) if i + 1 < len(segs) else ""
        out = vdir / f"seg{i + 1:02d}_{seg.beat}.mp3"
        if s.dry_run:
            # Silence as long as the text would take to say, so assembly timing is realistic.
            media.silence(out, max(0.6, tamil_letters(text) / s["episode"]["narration_letters_per_second"]))
            alignment, cached = None, False
        else:
            vid = voice_for(s, seg.speaker)
            cache_file = s.path("cache") / "voice_audio"
            res = ledger.run(
                episode_id=episode_id, step="voice",
                inputs={"voice": vid, "model": s["voice"]["model"], "text": text, "prev": prev, "next": nxt,
                        "settings": [s["voice"]["stability"], s["voice"]["similarity_boost"]]},
                estimate_usd=len(text) / 1000 * s["voice"]["price_per_1k_chars"],
                call=lambda: _tts(s, vid, text, prev, nxt, cache_file / f"{episode_id}_{out.name}"),
                force=force,
            )
            src = Path(res.value["file"])
            if not src.exists():  # cache entry without its audio: pay again rather than fail
                res = ledger.run(episode_id=episode_id, step="voice", inputs={"retry": str(src)}, estimate_usd=0.01,
                                 call=lambda: _tts(s, vid, text, prev, nxt, src), force=True)
            out.write_bytes(src.read_bytes())
            alignment, cached = res.value.get("alignment"), res.cached
            spent += res.cost_usd
        dur = media.duration(out)
        (vdir / f"{out.stem}.alignment.json").write_text(
            json.dumps({"text_written": seg.narration_ta, "text_spoken": text, "alignment": alignment},
                       ensure_ascii=False, indent=1), "utf-8")
        items.append({"n": i + 1, "beat": seg.beat, "speaker": seg.speaker, "file": out.name,
                      "seconds": round(dur, 3), "planned": [seg.start_s, seg.end_s], "cached": cached})

    manifest = {"dry_run": s.dry_run, "model": s["voice"]["model"], "segments": items, "cost_usd": round(spent, 4)}
    (vdir / "voice.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    return manifest
