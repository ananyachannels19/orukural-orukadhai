"""Phase 2 paid paths, exercised against fake Gemini/ElevenLabs clients (no network, no spend)."""

import base64
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orukural import assemble, config, continuity, media, visuals, voice
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
    for item in ("config.yaml", "data", "prompts", "assets/brand", "assets/fonts"):
        src = ROOT / item
        (tmp_path / item).parent.mkdir(parents=True, exist_ok=True)
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
    assert (ep / "render" / "K0301_draft.mp4").exists() and t["story_seconds"] >= 35
    # the signature: the kural on a slim palm leaf while it is said, a 2 s logo ending after the story
    assert t["signature"] and abs(t["total_seconds"] - t["story_seconds"] - 2.0) < 0.01
    assert abs(media.duration(ep / "render" / "K0301_draft.mp4") - t["total_seconds"]) < 0.2
    assert (ep / "render" / "kural_leaf.png").exists()
    assert (ep / "render" / "natural_sound.wav").exists()  # the clips' own sound goes under the voice
    # second run: everything comes from the cache, nothing is paid for again
    voice.generate(studio, ep, sc, "K0301")
    visuals.generate(studio, ep, sc, "K0301")
    assert calls == {"image": 20, "video": 4, "tts": 9}
    # an ffmpeg without libass (Homebrew's) still gets the same subtitles, as overlaid images
    from orukural import captions
    monkeypatch.setattr(captions, "ffmpeg_has_ass", lambda: False)
    assemble.assemble(studio, ep, sc, "K0301")
    pngs = list((ep / "render" / "subs").glob("sub*.png"))
    assert len(pngs) > len(sc.segments)  # long lines come one row at a time
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
    assert "4 characters on screen" in text and "no outfit in continuity for meena" in text
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
    # what the SDK really sends: a bare dict here lost the voice, so every line came out in one default voice
    from google.genai._gaos.types.interactions.generationconfig import GenerationConfig
    wire = [GenerationConfig.model_validate(sent[i]["generation_config"]).model_dump(exclude_none=True) for i in (0, 1, 3)]
    assert [w["speech_config"][0]["voice"] for w in wire] == ["Leda", "Charon", "Algenib"]
    assert all(w["speech_config"][0]["language"] == "ta-IN" for w in wire)
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


def test_flow_project_per_episode(studio):
    assert visuals.flow_project(studio, "K0301")["url"].startswith("https://flow.google.com/project/")
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0788/script.json").read_text("utf-8"))["script"])
    other = visuals.flow_project(studio, "K0788", sc)
    assert other["url"] is None and other["name"] == "K0788 – The friend at the gate at 3 am"
    ep = studio.path("episodes") / "K0788"
    visuals.flow_sheet(studio, ep, sc, "K0788")
    assert "No Flow project yet for K0788" in (ep / "flow" / "README.md").read_text("utf-8")
    visuals.record_flow_project(studio, "K0788", "https://flow.google.com/project/abc")
    assert config.load(studio.root / "config.yaml")["flow"]["projects"]["K0788"] == "https://flow.google.com/project/abc"
    assert "# One Flow project per episode" in (studio.root / "config.yaml").read_text("utf-8")  # comments kept
    sheet = visuals.flow_sheet(studio, ep, sc, "K0788")
    assert sheet["flow_project"] == "https://flow.google.com/project/abc"


def test_reference_cap(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    refs = continuity.shot_refs(studio, studio.path("episodes") / "K0301", sc, sc.shots[5])
    assert [lab for lab, _ in refs] == ["Kavin", "Thatha", "the place (thatha_thinnai)"]


def test_captions_one_style_one_row_at_a_time(studio, tmp_path):
    from orukural import captions
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    segs = [{"start": g.start_s, "end": g.end_s, "voice_seconds": g.end_s - g.start_s - 0.5} for g in sc.segments]
    ass = captions.write_ass(studio, sc, segs, sc.segments[-1].end_s, tmp_path / "c.ass").read_text("utf-8")
    events = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
    assert len(events) > len(sc.segments) and all(",Sub," in l and "\\N" not in l for l in events)
    # rows follow one another and never overlap
    cues = captions.cues(studio, sc, segs, sc.segments[-1].end_s)
    assert all(a < b <= nxt for (_, a, b), (_, nxt, _) in zip(cues, cues[1:]))
    from PIL import Image, ImageDraw
    d, font = ImageDraw.Draw(Image.new("RGBA", (1, 1))), captions._font(studio)
    assert all(d.textlength(row, font=font) <= captions.WIDTH for row, _, _ in cues)
    assert sum(l.startswith("Style:") for l in ass.splitlines()) == 1


def test_clip_prompts_say_who_talks(studio):
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    by_n = {sh.n: sh for sh in sc.shots}
    # Thatha's whole line is in shot 5: Flow says the real words (lip sync), and the clip gets room for them
    p5 = continuity.clip_prompt(studio, sc, by_n[5], 8)
    assert "Thatha says this line aloud in the deep" in p5 and sc.segments[3].narration_ta.strip() in p5
    assert "pronouncing every word exactly" in p5
    assert visuals.clip_seconds(studio, by_n[5], sc) >= 5
    # the kural runs on past shot 7, so there Thatha only mimes it
    assert "Thatha is talking" in continuity.clip_prompt(studio, sc, by_n[7], 4)
    # Thatha recites over a close-up of Kavin: Kavin's mouth must stay shut
    assert "nobody on screen talks" in continuity.clip_prompt(studio, sc, by_n[8], 4)
    assert "Kavin keeps their mouth closed" in continuity.clip_prompt(studio, sc, by_n[9], 8)
    assert "no voice or speech is heard" in continuity.clip_prompt(studio, sc, by_n[2], 8)
    _, warns = continuity.check(studio, sc)
    assert any("shot 8" in w and "wrong person" in w for w in warns)


def test_caption_rows_wait_for_a_pause_in_the_voice(tmp_path):
    from orukural import captions
    # 0.3 s quiet, 1.0 s voice, 0.8 s pause, 2.5 s voice: a short first row, a long second one
    wav = tmp_path / "v.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "sine=f=300:d=4.6,volume='if(between(t,0.3,1.3)+between(t,2.1,4.6),1,0)':eval=frame",
                    str(wav)], check=True)
    times = captions._row_times(["ஆஆஆஆ,", "ஆஆஆஆஆஆஆஆஆஆஆஆ"], 4.6, wav)
    assert abs(times[0] - 0.3) < 0.1     # first row waits for the first word
    assert 1.9 < times[1] < 2.15         # second row comes up as the voice resumes, not at the length split


def test_caption_rows_ignore_a_pause_inside_a_row(tmp_path):
    from orukural import captions
    # "என்ன, ஸ்கூல்ல யாராவது | திட்டினாங்களா? | அவங்க கிட்ட ஏன் கத்தல?" with a breath after என்ன,
    talk = "between(t,0,0.4)+between(t,0.75,1.9)+between(t,2.1,2.9)+between(t,3.2,4.6)"
    wav = tmp_path / "v.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=300:d=4.6,volume='if({talk},1,0)':eval=frame", str(wav)], check=True)
    rows = ["என்ன, ஸ்கூல்ல யாராவது", "திட்டினாங்களா?", "அவங்க கிட்ட ஏன் கத்தல?"]
    times = captions._row_times(rows, 4.6, wav)
    assert 1.9 <= times[1] <= 2.15 and 2.9 <= times[2] <= 3.25, times


def test_caption_short_row_before_a_pause_gets_its_word(tmp_path):
    from orukural import captions
    # "வள்ளுவர் என்ன சொல்றார் | தெரியுமா? | (pause) | செல்லிடத்துக் காப்பான் | சினங்காப்பான்,"
    talk = "between(t,0,2.1)+between(t,2.75,5.6)"
    wav = tmp_path / "v.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=300:d=5.6,volume='if({talk},1,0)':eval=frame", str(wav)], check=True)
    rows = ["வள்ளுவர் என்ன சொல்றார்", "தெரியுமா?", "செல்லிடத்துக் காப்பான்", "சினங்காப்பான்,"]
    times = captions._row_times(rows, 5.6, wav)
    assert times[1] < 1.8 and 2.6 <= times[2] <= 2.8, times   # தெரியுமா? is up while it is said
    # K0301 line 7 as heard: the question takes longer than its letters suggest, and the pause comes
    # nearer the split before தெரியுமா? than after it; the ? still claims it
    talk = "between(t,0,1.31)+between(t,1.95,5.6)"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=300:d=5.6,volume='if({talk},1,0)':eval=frame", str(wav)], check=True)
    rows = ["வள்ளுவர் என்ன சொல்றார்", "தெரியுமா?", "செல்லிடத்துக் காப்பான்", "சினங்காப்பான்,",
            "அல்லிடத்துக் காக்கின்என்", "காவாக்கா லென்?"]
    times = captions._row_times(rows, 5.6, wav)
    assert times[1] < 1.1 and 1.8 <= times[2] <= 1.95, times


def test_caption_row_without_punctuation_still_takes_a_close_pause(tmp_path):
    from orukural import captions
    # K0301 line 2: "...வாலாட்டி ஓடி வந்த குட்டி மேல | அந்தக் கோபம்..." pauses ~0.3 s of speech past the split
    talk = "between(t,0,2.6)+between(t,3.0,5.0)"
    wav = tmp_path / "v.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=300:d=5.0,volume='if({talk},1,0)':eval=frame", str(wav)], check=True)
    times = captions._row_times(["ஆஆஆஆஆஆஆஆஆ", "ஆஆஆஆஆஆஆஆஆ"], 5.0, wav)
    assert 2.85 <= times[1] <= 3.0, times


def test_lipsync_lays_our_voice_on_flows_speech(studio, tmp_path):
    from orukural import lipsync
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    shot6 = next(sh for sh in sc.shots if sh.n == 6)
    assert lipsync.spoken_lines(sc, shot6) == [4, 5]  # Kavin's line, then Thatha's reply
    ep = tmp_path / "K0301"
    (ep / "voice").mkdir(parents=True)
    (ep / "clips").mkdir()

    def tone(out, talk, d, video=False):
        src = ["-f", "lavfi", "-i", f"sine=f=300:d={d},volume='if({talk},1,0)':eval=frame"]
        if video:
            src = ["-f", "lavfi", "-i", f"color=c=gray:s=72x128:d={d}"] + src + ["-shortest", "-c:v", "libx264"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *src, str(out)], check=True)

    # Flow: Kavin speaks 0.8-2.6 s, Thatha 3.3-5.1 s of an 8 s clip
    tone(ep / "clips" / "shot06.mp4", "between(t,0.8,2.6)+between(t,3.3,5.1)", 8, video=True)
    # ours: 0.2 s of lead-in, then 2.0 s of speech each
    tone(ep / "voice" / "seg05.wav", "between(t,0.2,2.2)", 2.4)
    tone(ep / "voice" / "seg06.wav", "between(t,0.2,2.2)", 2.4)
    segs = [{"n": i + 1, "file": f"seg{i + 1:02d}.wav", "start": g.start_s, "end": g.end_s,
             "voice_seconds": g.end_s - g.start_s - 0.5} for i, g in enumerate(sc.segments)]
    spans = [(sh, sh.start_s, sh.end_s) for sh in sc.shots]
    out, offsets, notes = lipsync.fit(studio, ep, sc, segs, spans, {6: ep / "clips" / "shot06.mp4"})
    # the picture starts 0.8 s into the clip so Kavin's first word lands on his line at 19 s
    assert abs(offsets[6] - 0.8) < 0.1, notes
    assert abs(out[4]["start"] - 19.0) < 0.1 and abs(out[5]["start"] - 21.5) < 0.1, notes
    # each voice is squeezed from 2.0 s to Flow's 1.8 s
    assert abs(out[4]["voice_seconds"] - 1.8) < 0.1 and out[4]["lipsync"]["shot"] == 6
    assert out[3] == segs[3]  # other lines untouched
    # or keep Flow's own voice for that shot: the line plays straight from the clip, at the same moment
    (ep / "lipsync.json").write_text('{"flow_voice": [6]}')
    out2, _, _ = lipsync.fit(studio, ep, sc, segs, spans, {6: ep / "clips" / "shot06.mp4"})
    assert out2[4]["lipsync"]["voice"] == "flow" and abs(out2[4]["start"] - 18.95) < 0.1
    assert abs(out2[4]["voice_seconds"] - 1.9) < 0.1


def test_lipsync_fits_each_phrase_onto_flows(studio, tmp_path):
    from orukural import edit, lipsync
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    ep = tmp_path / "K0301"
    (ep / "voice").mkdir(parents=True)
    (ep / "clips").mkdir()

    def tone(out, talk, d, video=False):
        src = ["-f", "lavfi", "-i", f"sine=f=300:d={d},volume='if({talk},1,0)':eval=frame"]
        if video:
            src = ["-f", "lavfi", "-i", f"color=c=gray:s=72x128:d={d}"] + src + ["-shortest", "-c:v", "libx264"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *src, str(out)], check=True)

    # Flow: Kavin says two phrases with a long breath between (0.8-1.6, 2.6-3.4), Thatha 4.5-6.0
    clip = ep / "clips" / "shot06.mp4"
    tone(clip, "between(t,0.8,1.6)+between(t,2.6,3.4)+between(t,4.5,6.0)", 8, video=True)
    # ours: the same two phrases with only a short pause (0.2-1.0, 1.3-2.1)
    tone(ep / "voice" / "seg05.wav", "between(t,0.2,1.0)+between(t,1.3,2.1)", 2.4)
    tone(ep / "voice" / "seg06.wav", "between(t,0.2,1.7)", 2.0)
    segs = [{"n": i + 1, "file": f"seg{i + 1:02d}.wav", "start": g.start_s, "end": g.end_s,
             "voice_seconds": g.end_s - g.start_s - 0.5} for i, g in enumerate(sc.segments)]
    spans = [(sh, sh.start_s, sh.end_s) for sh in sc.shots]

    def sounds(f):
        gaps = media.pauses(f, min_seconds=0.12, noise_db=-40)
        return lipsync._parts(gaps, 0.0, media.duration(f))

    out, _, notes = lipsync.fit(studio, ep, sc, segs, spans, {6: clip})
    # our second phrase now starts where Flow's does, 1.8 s after the first: the mouth closes in our pause
    kavin = sounds(Path(out[4]["file"]))
    assert len(kavin) == 2 and abs(kavin[1][0] - 1.8) < 0.1, (kavin, notes)
    assert len(out[4]["lipsync"]["tempo"]) == 2
    # phrases pinned in the clip's own seconds still land right after a cut drops 1.7-2.4 s of the clip
    (ep / "lipsync.json").write_text('{"6": [[[0.8, 1.6], [2.6, 3.4]], [4.5, 6.0]]}')
    (ep / "edit.json").write_text('{"6": {"cut": [[1.7, 2.4]]}}')
    cut, moves = edit.prepare(studio, ep, sc, None, {6: clip})
    out2, _, _ = lipsync.fit(studio, ep, sc, segs, spans, cut, moves)
    assert out2[4]["lipsync"]["flow_speech"][1] == [1.9, 2.7]
    (a, b), = out2[5]["lipsync"]["flow_speech"]
    assert abs(a - 3.8) < 0.1 and abs(b - 5.3) < 0.1


def test_edit_cuts_sharpens_and_maps_time(studio, tmp_path):
    from PIL import features

    from orukural import edit
    assert edit.kept([[2, 3], [5, 9]], 8) == [(0, 2), (3, 5)]
    move = edit.to_clip(edit.kept([[2, 3]], 8))
    assert move(1.5) == 1.5 and move(2.5) == 2.0 and move(4.0) == 3.0
    ep = tmp_path / "K0301"
    (ep / "clips").mkdir(parents=True)
    _mp4(ep / "clips" / "shot06.mp4", secs=4)
    _mp4(ep / "clips" / "shot09.mp4", secs=2)
    spec = {"6": {"cut": [[1.0, 2.0]]}, "9": {"sharpen": {"box": [600, 400, 400, 600], "amount": 1.5}}}
    (ep / "edit.json").write_text(json.dumps(spec))
    sc = EpisodeScript.model_validate(json.loads((ROOT / "samples/K0301/script.json").read_text("utf-8"))["script"])
    clips = {n: ep / "clips" / f"shot{n:02d}.mp4" for n in (6, 9)}
    out, moves = edit.prepare(studio, ep, sc, None, clips)
    # the cut drops a second of picture and sound together, at the film's size
    assert abs(media.duration(out[6]) - 3.0) < 0.1 and media.has_audio(out[6])
    size = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", str(out[9])], capture_output=True, text=True).stdout.strip()
    assert size == "1080,1920" and abs(media.duration(out[9]) - 2.0) < 0.1
    assert moves[6](1.5) == 1.0 and moves[6](2.5) == 1.5 and moves[9](1.5) == 1.5
    if features.check("raqm"):  # the kural card needs Tamil shaping (studio.py sets that up on a Mac)
        kural = {"verse": {"line1": "செல்லிடத்துக் காப்பான் சினங்காப்பான் அல்லிடத்துக்", "line2": "காக்கின்என் காவாக்கா லென்?"}}
        (ep / "edit.json").write_text('{"6": {"card": "kural"}}')
        out, _ = edit.prepare(studio, ep, sc, kural, clips)
        assert (ep / "render" / "edit" / "card06.png").exists() and media.duration(out[6]) > 3.9


def test_final_master_is_slower_and_nearer_lossless(studio):
    m = assemble.master(studio)
    assert (m["assembly"]["crf"], m["assembly"]["preset"], m["assembly"]["audio_kbps"]) == (16, "slow", 256)
    assert m["assembly"]["output_name"] == "final" and "output_name" not in studio["assembly"]
    enc = assemble._encode(m)
    assert enc[enc.index("-crf") + 1] == "16" and enc[enc.index("-preset") + 1] == "slow"
    assert studio["assembly"]["crf"] == 18  # the draft settings are left alone
    assert "flags=lanczos" in media.fill_frame()


def test_voice_pitch_tells_a_man_from_a_child(tmp_path):
    for hz in (110, 260):
        f = tmp_path / f"{hz}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        f"sine=f={hz}:d=1.5,aformat=channel_layouts=mono", str(f)], check=True)
        assert abs(media.median_pitch(f) - hz) < 8
