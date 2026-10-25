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

    store = KuralStore(studio.path("kurals"))
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = studio.path("episodes") / "K0301"
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    t = assemble.assemble(studio, ep, sc, "K0301")

    assert calls == {"image": 2 + 10, "video": 5, "tts": 9}
    assert (ep / "render" / "K0301_draft.mp4").exists() and t["total_seconds"] >= 35
    # second run: everything comes from the cache, nothing is paid for again
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    assert calls == {"image": 12, "video": 5, "tts": 9}
    spend = [json.loads(l) for l in studio.path("ledger").read_text().splitlines()]
    assert {e["step"] for e in spend} == {"character_ref", "image", "clip", "voice"}


def test_key_mode_picks_first_last_and_priorities(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    assert visuals.animated_shots(studio, sc) == {1, 10, 4, 6, 9}
    studio.raw["video"]["animate"] = "none"
    assert visuals.animated_shots(studio, sc) == set()


def test_remap_keeps_shots_with_their_segments():
    anchors = [(0, 0), (3, 3.5), (8, 9.0)]
    assert assemble.remap(3, anchors) == 3.5
    assert abs(assemble.remap(5.5, anchors) - 6.25) < 1e-9
