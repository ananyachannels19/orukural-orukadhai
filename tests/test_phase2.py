"""Phase 2 paid paths, exercised against fake Gemini/ElevenLabs clients (no network, no spend)."""

import base64
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orukural import assemble, config, continuity, visuals, voice
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
    studio.raw["continuity"]["require_review"] = False
    store = KuralStore(studio.path("kurals"))
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = studio.path("episodes") / "K0301"
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    t = assemble.assemble(studio, ep, sc, "K0301")

    # references: 2 characters + 4 places + 4 props, then 10 shot images
    assert calls == {"image": 2 + 4 + 4 + 10, "video": 4, "tts": 9}
    assert (ep / "render" / "K0301_draft.mp4").exists() and t["total_seconds"] >= 35
    # second run: everything comes from the cache, nothing is paid for again
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    assert calls == {"image": 20, "video": 4, "tts": 9}
    # an ffmpeg without libass (Homebrew's) still gets the same subtitles, as overlaid images
    from orukural import captions
    monkeypatch.setattr(captions, "ffmpeg_has_ass", lambda: False)
    assemble.assemble(studio, ep, sc, "K0301")
    assert len(list((ep / "render" / "subs").glob("sub*.png"))) == len(sc.segments)
    spend = [json.loads(l) for l in studio.path("ledger").read_text().splitlines()]
    assert {e["step"] for e in spend} == {"character_ref", "location_ref", "prop_ref", "image", "clip", "voice"}


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

    studio.raw["continuity"]["max_refs_per_image"] = 6
    sheet = visuals.flow_sheet(studio, ep, sc, "K0301")
    kinds = [j["kind"] for j in sheet["jobs"]]
    assert kinds.count("character_ref") == 2 and kinds.count("location_ref") == 4 and kinds.count("prop_ref") == 4
    assert kinds.count("image") == 10 and kinds.count("clip") == 10
    shot6 = next(j for j in sheet["jobs"] if j.get("shot") == 6 and j["kind"] == "image")
    assert shot6["reference_images"] == ["assets/characters/kavin.png", "assets/characters/thatha.png",
                                         "assets/locations/thatha_thinnai.png", "episodes/K0301/refs/props/puppy.png"]
    assert "one floppy left ear" in shot6["prompt"] and "no shawl" in shot6["prompt"]
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
    with pytest.raises(SystemExit, match="continuity review not passed"):
        assemble.assemble(studio, ep, sc, "K0301")
    made = continuity.contact_sheet(studio, ep, sc, ep / "flow" / "review")
    assert {p.name for p in made} >= {"images.jpg", "clip_frames.jpg"}
    review = continuity.load_review(ep)
    review["images"] = {k: "pass" for k in review["images"]}
    review["clips"] = {k: "pass" for k in review["clips"]}
    review["clips"]["4"] = "puppy's ear flips sides"
    (ep / continuity.REVIEW_FILE).write_text(json.dumps(review))
    with pytest.raises(SystemExit, match="clip shot 4: puppy"):
        assemble.assemble(studio, ep, sc, "K0301")
    review["clips"]["4"] = "pass"
    (ep / continuity.REVIEW_FILE).write_text(json.dumps(review))
    t = assemble.assemble(studio, ep, sc, "K0301")
    assert [x["source"] for x in t["shots"]].count("clip") == 10


def test_monthly_top_up_fits_an_episode_in_one_day(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = studio.path("episodes") / "K0301"
    plain = visuals.flow_sheet(studio, ep, sc, "K0301")
    assert plain["clip_days"] == 2 and plain["monthly_credits_used"] == 0
    topped = visuals.flow_sheet(studio, ep, sc, "K0301", pool=studio["flow"]["monthly_top_up_per_episode"])
    assert topped["clip_days"] == 1 and topped["monthly_credits_used"] == topped["clip_credits"] - studio["flow"]["daily_credits"]


def test_continuity_checks_catch_breaks(studio):
    raw = json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"]
    sc = EpisodeScript.model_validate(raw)
    errors, _ = continuity.check(studio, sc)
    assert errors == []
    raw["shots"][4]["location"] = "kitchen"                 # place not in the bible
    raw["shots"][5]["props"] = ["puppy", "kite"]            # prop not in the bible
    raw["shots"][2]["characters"] = ["kavin", "meena", "murugan_anna"]  # two supporting characters
    raw["shots"][5]["props"] = ["kite"]
    raw["continuity"]["props"].append({"id": "kite", "name_ta": "", "description_en": "a red kite"})
    raw["shots"][3]["props"] = ["red_backpack"]             # puppy gone while the narration names it
    raw["shots"][4]["characters"] = ["kavin"]               # Thatha speaks 15-19 s but is not on screen
    sc = EpisodeScript.model_validate(raw)
    errors, warns = continuity.check(studio, sc)
    text = " | ".join(errors + warns)
    assert "location 'kitchen'" in text
    assert "more than one supporting character" in text and "no outfit in continuity for meena" in text
    assert "dialogue mentions குட்டி (puppy) but no shot shows it" in text
    assert "thatha speaks but is not on screen" in text


def test_gemini_tts_free_voice(studio, tmp_path, monkeypatch):
    studio.raw["voice"]["provider"] = "gemini_tts"
    studio.raw["voice"]["gemini_tts"]["seconds_between_calls"] = 0
    wav = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=d=1.2", "-ar", "24000",
                    "-ac", "1", str(wav)], check=True)
    sent = []

    class Interactions:
        def create(self, **kw):
            sent.append(kw)
            return SimpleNamespace(id="a1", output_audio=SimpleNamespace(data=base64.b64encode(wav.read_bytes()).decode()))

    monkeypatch.setattr(voice, "_gemini_client", lambda *a: SimpleNamespace(interactions=Interactions()))
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = studio.path("episodes") / "K0301"
    m = voice.generate(studio, ep, sc, "K0301")
    assert len(sent) == 9 and m["cost_usd"] == 0
    assert sent[0]["model"] == "gemini-3.8-flash-tts" and sent[0]["response_format"]["type"] == "audio"
    # seg 1 is Kavin, seg 2 the narrator, seg 4 Thatha
    assert [sent[i]["generation_config"]["speech_config"]["voice"] for i in (0, 1, 3)] == ["Puck", "Charon", "Iapetus"]
    assert all(abs(x["seconds"] - 1.2) < 0.2 for x in m["segments"])


def test_gemini_tts_retries_a_hung_request(studio, tmp_path, monkeypatch):
    studio.raw["voice"]["provider"] = "gemini_tts"
    studio.raw["voice"]["gemini_tts"]["seconds_between_calls"] = 0
    wav = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=d=1", str(wav)], check=True)
    calls = []

    class ReadTimeout(Exception):
        pass

    class Interactions:
        def create(self, **kw):
            calls.append(1)
            if len(calls) == 1:
                raise ReadTimeout("The read operation timed out")
            return SimpleNamespace(id="a", output_audio=SimpleNamespace(data=base64.b64encode(wav.read_bytes()).decode()))

    monkeypatch.setattr(voice, "_gemini_client", lambda *a: SimpleNamespace(interactions=Interactions()))
    monkeypatch.setattr(voice.time, "sleep", lambda s: None)
    out = tmp_path / "x.mp3"
    voice._gemini(studio, "Charon", "வணக்கம்", out)
    assert len(calls) == 2 and out.exists()


def test_gemini_tts_stops_at_once_on_daily_limit(studio, tmp_path, monkeypatch):
    studio.raw["voice"]["provider"] = "gemini_tts"
    calls = []

    class Interactions:
        def create(self, **kw):
            calls.append(1)
            raise Exception("429 RESOURCE_EXHAUSTED. limit: 10 requests per day on Free Tier")

    monkeypatch.setattr(voice, "_gemini_client", lambda *a: SimpleNamespace(interactions=Interactions()))
    monkeypatch.setattr(voice.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="per day"):
        voice._gemini(studio, "Charon", "வணக்கம்", tmp_path / "x.mp3")
    assert len(calls) == 1


def test_flow_project_per_adhikaram(studio):
    assert visuals.flow_project(studio, 301)["url"].startswith("https://flow.google.com/project/")
    other = visuals.flow_project(studio, 151)  # adhikaram 16, no project yet
    assert other["adhikaram"] == 16 and other["url"] is None


def test_reference_cap(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    refs = continuity.shot_refs(studio, studio.path("episodes") / "K0301", sc, sc.shots[5])
    assert [lab for lab, _ in refs] == ["Kavin", "Thatha", "the place (thatha_thinnai)"]


def test_captions_one_style_one_line_at_a_time(studio, tmp_path):
    from orukural import captions
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    segs = [{"start": g.start_s, "end": g.end_s, "voice_seconds": g.end_s - g.start_s - 0.5} for g in sc.segments]
    ass = captions.write_ass(studio, sc, segs, sc.segments[-1].end_s, tmp_path / "c.ass").read_text("utf-8")
    events = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
    assert len(events) == len(sc.segments) and all(",Sub," in l for l in events)
    assert sum(l.startswith("Style:") for l in ass.splitlines()) == 1


def test_clip_prompts_say_who_talks(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    by_n = {sh.n: sh for sh in sc.shots}
    assert "Thatha is talking" in continuity.clip_prompt(studio, sc, by_n[5], 4)
    # Thatha recites over a close-up of Kavin: Kavin's mouth must stay shut
    assert "nobody on screen talks" in continuity.clip_prompt(studio, sc, by_n[8], 4)
    assert "Kavin keeps their mouth closed" in continuity.clip_prompt(studio, sc, by_n[9], 8)
    _, warns = continuity.check(studio, sc)
    assert any("shot 8" in w and "wrong person" in w for w in warns)
