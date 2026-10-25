"""Phase 2: Tamil narration, one audio file per script segment.

Providers (config `voice.provider`):
  gemini_tts  Gemini TTS on a free Google AI Studio key (no billing). Default.
  google_tts  Google Cloud Text-to-Speech, Chirp 3 HD Tamil voices. Needs Cloud billing.
  elevenlabs  ElevenLabs eleven_v4. Paid plan needed for commercial use.

Each segment is voiced on its own so we keep exact per-beat timing. Word timings for
subtitles come from ElevenLabs when used, otherwise from Whisper in phase 3.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

import requests
import yaml

from . import live, media
from .config import Settings
from .ledger import Ledger
from .schema import EpisodeScript, tamil_letters

ELEVEN_API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
GOOGLE_API = "https://texttospeech.googleapis.com/v1/text:synthesize"


def load_fixes(s: Settings) -> dict[str, str]:
    data = yaml.safe_load(s.file("pronunciation_file").read_text("utf-8")) or {}
    return data.get("fixes") or {}


def spoken_text(text: str, fixes: dict[str, str]) -> str:
    """Apply pronunciation respellings (longest first) and drop on-screen-only symbols."""
    for written in sorted(fixes, key=len, reverse=True):
        text = text.replace(written, fixes[written])
    return re.sub(r"[➜→•]", "", text).strip()


def provider_cfg(s: Settings) -> tuple[str, dict]:
    name = s["voice"]["provider"]
    return name, s["voice"][name]


def voice_for(s: Settings, speaker: str) -> str:
    name, cfg = provider_cfg(s)
    default = cfg["voice_id"] if name == "elevenlabs" else cfg["voice"]
    vid = (cfg.get("speaker_voices") or {}).get(speaker) or default
    if not vid:
        raise SystemExit(f"no voice set for {speaker!r} in config.yaml voice.{name}")
    return vid


def _google_key() -> str:
    key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GOOGLE_TTS_API_KEY is not set (or GEMINI_API_KEY with the Text-to-Speech API enabled). "
                         "Add it to .env, or run with --dry-run.")
    return key


def _google(s: Settings, voice: str, text: str, out: Path) -> tuple[dict, float, dict]:
    cfg = s["voice"]["google_tts"]
    r = requests.post(
        GOOGLE_API,
        params={"key": _google_key()},
        json={
            "input": {"text": text},
            "voice": {"languageCode": voice.split("-Chirp")[0] if "-" in voice else "ta-IN", "name": voice},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": cfg["speaking_rate"]},
        },
        timeout=120,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Google TTS {r.status_code}: {r.text[:500]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(r.json()["audioContent"]))
    return {"file": str(out), "alignment": None}, len(text) / 1000 * cfg["price_per_1k_chars"], {
        "provider": "google_tts", "model": voice, "chars": len(text)}


def _gemini_client(timeout_s: float = 90):
    from google import genai
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY is not set. Make a free key at aistudio.google.com/apikey, add it to .env, "
                         "or run with --dry-run.")
    # A hard timeout: on the free tier a throttled request can otherwise hang with no error.
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"timeout": int(timeout_s * 1000)})


_last_call = [0.0]


def _gemini(s: Settings, voice: str, text: str, out: Path) -> tuple[dict, float, dict]:
    cfg = s["voice"]["gemini_tts"]
    client = _gemini_client(cfg.get("timeout_seconds", 90))
    tries = cfg.get("retries", 5)
    for attempt in range(tries):
        # Free tier allows only a few requests a minute: keep calls spaced out.
        wait = cfg.get("seconds_between_calls", 0) - (time.monotonic() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()
        try:
            interaction = client.interactions.create(
                model=cfg["model"],
                input=[{"type": "text", "text": text}],
                response_format={"type": "audio", "mime_type": "audio/wav"},
                generation_config={"speech_config": {"voice": voice, "language": cfg["language"]}},
            )
            break
        except Exception as e:  # rate limit or a hung request: back off and try again
            msg = str(e)
            retryable = any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")) \
                or "timeout" in type(e).__name__.lower() or "timed out" in msg.lower()
            if not retryable or attempt == tries - 1:
                raise RuntimeError(f"Gemini TTS failed for {out.name} after {attempt + 1} tries: {msg[:300]}") from e
            print(f"  voice: {type(e).__name__}, waiting {60 * (attempt + 1)} s (free-tier limit?)", flush=True)
            time.sleep(60 * (attempt + 1))
    audio = interaction.output_audio
    if not audio or not audio.data:
        raise RuntimeError(f"no audio returned for {out.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.with_suffix(".wav")
    wav.write_bytes(base64.b64decode(audio.data))
    media.run(["-i", str(wav), "-c:a", "libmp3lame", "-q:a", "2", str(out)])
    wav.unlink()
    return {"file": str(out), "alignment": None}, 0.0, {
        "provider": "gemini_tts", "model": cfg["model"], "voice": voice, "chars": len(text),
        "interaction_id": getattr(interaction, "id", None)}


def _eleven(s: Settings, voice_id: str, text: str, prev: str, nxt: str, out: Path) -> tuple[dict, float, dict]:
    cfg = s["voice"]["elevenlabs"]
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise SystemExit("ELEVENLABS_API_KEY is not set. Add it to .env, or run with --dry-run.")
    body = {
        "text": text,
        "model_id": cfg["model"],
        "previous_text": prev or None,
        "next_text": nxt or None,
        "voice_settings": {"stability": cfg["stability"], "similarity_boost": cfg["similarity_boost"]},
        "seed": 1330,
    }
    if not cfg["model"].startswith("eleven_multilingual"):
        body["language_code"] = s["voice"]["language_code"]
    r = requests.post(
        ELEVEN_API.format(voice_id=voice_id),
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
    return {"file": str(out), "alignment": data.get("alignment")}, len(text) / 1000 * cfg["price_per_1k_chars"], {
        "provider": "elevenlabs", "model": cfg["model"], "chars": len(text), "request_id": r.headers.get("request-id")}


def synthesize(s: Settings, ledger: Ledger, episode_id: str, speaker: str, text: str, prev: str, nxt: str,
               cache_name: str, force: bool = False):
    name, cfg = provider_cfg(s)
    vid = voice_for(s, speaker)
    cache_file = s.path("cache") / "voice_audio" / cache_name
    if name == "gemini_tts":
        inputs = {"provider": name, "model": cfg["model"], "voice": vid, "text": text}
        call = lambda: _gemini(s, vid, text, cache_file)  # noqa: E731
    elif name == "google_tts":
        inputs = {"provider": name, "voice": vid, "rate": cfg["speaking_rate"], "text": text}
        call = lambda: _google(s, vid, text, cache_file)  # noqa: E731
    else:
        inputs = {"provider": name, "voice": vid, "model": cfg["model"], "text": text, "prev": prev, "next": nxt,
                  "settings": [cfg["stability"], cfg["similarity_boost"]]}
        call = lambda: _eleven(s, vid, text, prev, nxt, cache_file)  # noqa: E731
    res = ledger.run(episode_id=episode_id, step="voice", inputs=inputs,
                     estimate_usd=len(text) / 1000 * cfg["price_per_1k_chars"], call=call, force=force)
    if not Path(res.value["file"]).exists():  # cache entry lost its audio file: make it again
        res = ledger.run(episode_id=episode_id, step="voice", inputs=inputs, estimate_usd=0.0, call=call, force=True)
    return res


def generate(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str, force: bool = False) -> dict:
    """Voice every segment; returns and writes voice/voice.json with real durations."""
    media.require_ffmpeg()
    vdir = ep_dir / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    fixes = load_fixes(s)
    segs = script.segments
    ledger = Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])

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
            try:
                res = synthesize(s, ledger, episode_id, seg.speaker, text, prev, nxt, f"{episode_id}_{out.name}", force)
            except Exception as e:
                quota = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                live.emit(s, episode_id, "voice", "wait" if quota else "fail", f"line {i + 1}: {str(e)[:200]}")
                raise
            if not res.cached:
                live.emit(s, episode_id, "voice", "done", f"line {i + 1} ({seg.speaker})", requests=1)
            out.write_bytes(Path(res.value["file"]).read_bytes())
            alignment, cached = res.value.get("alignment"), res.cached
            spent += res.cost_usd
        dur = media.duration(out)
        (vdir / f"{out.stem}.alignment.json").write_text(
            json.dumps({"text_written": seg.narration_ta, "text_spoken": text, "alignment": alignment},
                       ensure_ascii=False, indent=1), "utf-8")
        items.append({"n": i + 1, "beat": seg.beat, "speaker": seg.speaker, "file": out.name,
                      "seconds": round(dur, 3), "planned": [seg.start_s, seg.end_s], "cached": cached})

    manifest = {"dry_run": s.dry_run, "provider": s["voice"]["provider"], "segments": items, "cost_usd": round(spent, 4)}
    (vdir / "voice.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    return manifest


def voice_test(s: Settings, text: str, voices: list[str], out_dir: Path) -> list[Path]:
    """Say one line in several voices so you can pick by ear (free on Gemini TTS and Google TTS)."""
    name, _ = provider_cfg(s)
    ledger = Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])
    outs = []
    for v in voices:
        out = out_dir / f"{v}.mp3"
        if name == "gemini_tts":
            res = ledger.run(episode_id="VOICE_TEST", step="voice", inputs={"tts": name, "voice": v, "text": text},
                             estimate_usd=0.0, call=lambda: _gemini(s, v, text, s.path("cache") / "voice_test" / out.name))
        elif name == "google_tts":
            res = ledger.run(episode_id="VOICE_TEST", step="voice", inputs={"voice": v, "text": text},
                             estimate_usd=0.0, call=lambda: _google(s, v, text, s.path("cache") / "voice_test" / out.name))
        else:
            res = ledger.run(episode_id="VOICE_TEST", step="voice", inputs={"voice": v, "text": text},
                             estimate_usd=0.01, call=lambda: _eleven(s, v, text, "", "", s.path("cache") / "voice_test" / out.name))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(Path(res.value["file"]).read_bytes())
        outs.append(out)
    return outs
