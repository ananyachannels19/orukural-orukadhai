"""Phase 2 paid paths, exercised against fake Gemini/ElevenLabs clients (no network, no spend)."""

import base64
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orukural import assemble, config, visuals, voice
from orukural.kurals import KuralStore
from orukural.schema import EpisodeScript

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")


def _png(path: Path):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=orange:s=576x1024",
                    "-frames:v", "1", str(path)], check=True)
    return path.read_bytes()


def _mp4(path: Path, secs=4):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=s=720x1280:d={secs}",
                    "-f", "lavfi", "-i", f"sine=d={secs}", "-shortest", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path.read_bytes()


def _mp3(path: Path, secs=1.5):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"sine=d={secs}", str(path)], check=True)
    return path.read_bytes()


@pytest.fixture
def studio(tmp_path, monkeypatch):
    for item in ("config.yaml", "data", "prompts"):
        src = ROOT / item
        (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp_path / item)
    s = config.load(tmp_path / "config.yaml", dry_run=False)
    s.raw["budget"]["per_episode_cap"] = 50
    s.raw["images"]["provider"] = s.raw["video"]["provider"] = "gemini"
    s.raw["voice"]["provider"] = "elevenlabs"
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake")
    return s


def test_paid_render_path_with_fakes(studio, tmp_path, monkeypatch):
    png, mp4, mp3 = _png(tmp_path / "a.png"), _mp4(tmp_path / "a.mp4"), _mp3(tmp_path / "a.mp3")
    calls = {"image": 0, "video": 0, "tts": 0}

    class Interactions:
        def create(self, **kw):
            if kw["response_format"]["type"] == "image":
                calls["image"] += 1
                assert kw["model"] == "gemini-nano-banana-2.1"
                return SimpleNamespace(id="i1", output_image=SimpleNamespace(data=base64.b64encode(png).decode()))
            calls["video"] += 1
            assert kw["generation_config"]["video_config"]["task"] == "image_to_video"
            assert kw["response_format"]["aspect_ratio"] == "9:16"
            return SimpleNamespace(id="v1", output_video=SimpleNamespace(data=None, uri="https://x/v1beta/files/abc:download?alt=media"))

    class Files:
        def get(self, name):
            assert name == "files/abc"
            return SimpleNamespace(state=SimpleNamespace(name="ACTIVE"))

        def download(self, file):
            return mp4

    monkeypatch.setattr(visuals, "_client", lambda: SimpleNamespace(interactions=Interactions(), files=Files()))

    def fake_post(url, params, headers, json, timeout):
        calls["tts"] += 1
        assert json["model_id"] == "eleven_v4" and json["language_code"] == "ta"
        body = {"audio_base64": base64.b64encode(mp3).decode(), "alignment": {"characters": list(json["text"])}}
        return SimpleNamespace(status_code=200, json=lambda: body, headers={}, text="")

    monkeypatch.setattr(voice.requests, "post", fake_post)

    studio.raw["video"]["animate"] = "key"  # 4 paid clips, the rest held stills
    studio.raw["assembly"]["missing_clip"] = "still"
    store = KuralStore(studio.path("kurals"))
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = studio.path("episodes") / "K0301"
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    t = assemble.assemble(studio, ep, sc, "K0301")

    assert calls == {"image": 2 + 10, "video": 4, "tts": 9}
    assert (ep / "render" / "K0301_draft.mp4").exists() and t["total_seconds"] >= 35
    # second run: everything comes from the cache, nothing is paid for again
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    assert calls == {"image": 12, "video": 4, "tts": 9}
    spend = [json.loads(l) for l in studio.path("ledger").read_text().splitlines()]
    assert {e["step"] for e in spend} == {"character_ref", "image", "clip", "voice"}


def test_key_mode_picks_first_last_and_priorities(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    assert visuals.animated_shots(studio, sc) == set(range(1, 11))  # default: every shot
    studio.raw["video"]["animate"] = "key"
    assert visuals.animated_shots(studio, sc) == {1, 10, 4, 6}
    studio.raw["video"]["animate"] = "none"
    assert visuals.animated_shots(studio, sc) == set()


def test_remap_keeps_shots_with_their_segments():
    anchors = [(0, 0), (3, 3.5), (8, 9.0)]
    assert assemble.remap(3, anchors) == 3.5
    assert abs(assemble.remap(5.5, anchors) - 6.25) < 1e-9


def test_free_mode_google_tts_and_flow(studio, tmp_path, monkeypatch):
    studio.raw["images"]["provider"] = studio.raw["video"]["provider"] = "flow"
    studio.raw["voice"]["provider"] = "google_tts"
    monkeypatch.setenv("GOOGLE_TTS_API_KEY", "fake")
    mp3 = _mp3(tmp_path / "a.mp3")
    sent = []

    def fake_post(url, params, json, timeout):
        sent.append(json["voice"])
        return SimpleNamespace(status_code=200, json=lambda: {"audioContent": base64.b64encode(mp3).decode()}, text="")

    monkeypatch.setattr(voice.requests, "post", fake_post)
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = studio.path("episodes") / "K0301"

    sheet = visuals.flow_sheet(studio, ep, sc, "K0301")
    kinds = [j["kind"] for j in sheet["jobs"]]
    assert kinds.count("character_ref") == 2 and kinds.count("image") == 10 and kinds.count("clip") == 10
    daily = studio["flow"]["daily_credits"]
    per_day = {}
    for j in sheet["jobs"]:
        if j["kind"] == "clip":
            per_day[j["day"]] = per_day.get(j["day"], 0) + j["credits"]
    assert sheet["clip_days"] == len(per_day) >= 2 and max(per_day.values()) <= daily

    with pytest.raises(SystemExit):  # nothing made in Flow yet
        visuals.generate(studio, ep, sc, "K0301")
    (ep / "images").mkdir(parents=True)
    for n in range(1, 11):
        _png(ep / "images" / f"shot{n:02d}.jpg")
    (ep / "clips").mkdir()
    _mp4(ep / "clips" / "shot01.mp4")  # day 1 only partly done
    (studio.root / "assets" / "characters").mkdir(parents=True, exist_ok=True)
    for cid in ("thatha", "kavin"):
        _png(studio.root / "assets" / "characters" / f"{cid}.png")

    m = visuals.generate(studio, ep, sc, "K0301")
    assert m["animated_made"] == [1]
    voice.generate(studio, ep, sc, "K0301")
    # seg 1 is Kavin, seg 2 the narrator, seg 4 Thatha
    assert [sent[i]["name"] for i in (0, 1, 3)] == [
        "ta-IN-Chirp3-HD-Puck", "ta-IN-Chirp3-HD-Charon", "ta-IN-Chirp3-HD-Iapetus"]
    assert all(v["languageCode"] == "ta-IN" for v in sent)
    with pytest.raises(SystemExit, match="waiting for clips"):  # never zooms over a still: waits for credits
        assemble.assemble(studio, ep, sc, "K0301")
    for n in range(2, 11):  # next day's credits
        _mp4(ep / "clips" / f"shot{n:02d}.mp4")
    visuals.generate(studio, ep, sc, "K0301")
    t = assemble.assemble(studio, ep, sc, "K0301")
    assert [x["source"] for x in t["shots"]].count("clip") == 10
