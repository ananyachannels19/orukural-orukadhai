"""The 3-a-week plan: a new cast per episode, voices per story, clip reuse, the credit cap, the posting
package and the channel signature."""

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from orukural import config, continuity, lipsync, publish, scriptgen, signature, visuals, voice
from orukural.kurals import KuralStore
from orukural.schema import EpisodeScript, check

ROOT = Path(__file__).resolve().parents[1]
ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")


@pytest.fixture
def studio(tmp_path):
    for item in ("config.yaml", "data", "prompts", "assets/brand", "assets/fonts"):
        src = ROOT / item
        (tmp_path / item).parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp_path / item)
    shutil.rmtree(tmp_path / "assets/brand/signature", ignore_errors=True)  # built fresh by the test
    return config.load(tmp_path / "config.yaml", dry_run=False)


@pytest.fixture
def k788():
    return json.loads((ROOT / "samples/K0788/script.json").read_text("utf-8"))["script"]


def _without_appa(raw):
    """K0788 with only the two friends, leaving room for another character."""
    raw["cast"] = [c for c in raw["cast"] if c["id"] != "appa"]
    for sh in raw["shots"]:
        sh["characters"] = [c for c in sh["characters"] if c != "appa"]
    return raw


def _checks(s, raw):
    sc = EpisodeScript.model_validate(raw)
    store = KuralStore(s.path("kurals"))
    e1, w1 = check(sc, store.get(sc.kural_number), s.raw)
    e2, w2 = continuity.check(s, sc)
    return e1 + e2 + visuals.credit_check(s, sc), w1 + w2


def test_k0788_passes_every_check(studio, k788):
    errors, warns = _checks(studio, k788)
    assert errors == [] and warns == []
    sc = EpisodeScript.model_validate(k788)
    plan = visuals.clip_plan(studio, sc)
    assert len(plan) == 7 and sum(c["credits"] for c in plan) <= studio["budget"]["per_reel_credits"]
    assert all(g.speaker == "narrator" for g in sc.segments if g.beat == "kural")


def test_no_fixed_cast_left_in_the_code():
    for f in ("schema.py", "continuity.py", "visuals.py", "scriptgen.py"):
        text = (ROOT / "orukural" / f).read_text("utf-8")
        assert "MAIN_CHARACTERS" not in text and "Thatha and Kavin must" not in text
    schema = (ROOT / "prompts/episode_script.schema.json").read_text("utf-8")
    assert '"thatha"' not in schema and "cast" in schema


def test_cast_rules(studio, k788):
    raw = copy.deepcopy(k788)
    raw["cast"][0]["age"] = 45                      # outside the adult range
    raw["cast"][1]["voice"] = "Kore"                # a woman's voice for a man
    errors, _ = _checks(studio, raw)
    text = " | ".join(errors)
    assert "vignesh is 45" in text and "saro is male but Kore is a female voice" in text

    raw = copy.deepcopy(k788)
    raw["cast"][1]["voice"] = "Charon"
    assert any("narrator's voice" in e for e in _checks(studio, raw)[0])
    raw["cast"][1]["voice"] = "Achird"              # both share one voice
    assert any("share a voice" in e for e in _checks(studio, raw)[0])


def test_one_child_when_the_story_needs_one(studio, k788):
    raw = _without_appa(copy.deepcopy(k788))
    raw["cast"].append({"id": "nila", "name_ta": "நிலா", "age": 7, "job": "school girl", "gender": "female",
                        "age_group": "child", "look_en": "x", "outfit_en": "y", "voice": "Kore"})
    raw["shots"][7]["characters"] = ["saro", "vignesh", "nila"]
    errors, _ = _checks(studio, raw)
    assert any("nila is a child: pick one of the young voices" in e for e in errors)
    raw["cast"][2]["voice"] = "Leda"
    assert _checks(studio, raw)[0] == []           # a child with a young voice is fine
    raw["cast"].append({**raw["cast"][2], "id": "kuttan", "voice": "Puck", "gender": "male"})
    raw["shots"][6]["characters"] = ["saro", "kuttan"]
    errors, _ = _checks(studio, raw)
    assert any("2 children" in e for e in errors)


def test_thatha_cameo(studio, k788):
    raw = copy.deepcopy(k788)
    raw["shots"][6]["characters"] = ["saro", "vignesh", "thatha"]
    assert any("set thatha_cameo" in e for e in _checks(studio, raw)[0])
    raw["thatha_cameo"] = True
    assert _checks(studio, raw)[0] == []           # he doesn't count towards the 2-3
    sc = EpisodeScript.model_validate(raw)
    prompt = continuity.image_prompt(studio, sc, sc.shots[6], [])
    assert "phone or laptop screen" in prompt and "silver hair" in prompt
    refs = continuity.shot_refs(studio, studio.root / "episodes/K0788", sc, sc.shots[6])
    assert str(refs[2][1]).endswith("assets/characters/thatha.png")  # his series reference, reused
    raw["shots"][5]["characters"] = ["saro", "kavin"]
    assert any("series characters ['kavin']" in e for e in _checks(studio, raw)[0])
    # his voice stays his; the cast log neither flags nor records him as cast
    assert voice.voice_for(studio, "thatha", sc) == "Algenib"
    continuity.log_cast(studio, sc, "K0788")
    entry = continuity.cast_log(studio)[-1]
    assert entry["cameo"] == "thatha" and [c["id"] for c in entry["characters"]] == ["vignesh", "saro", "appa"]


def test_cast_log_flags_repeats(studio, k788):
    sc = EpisodeScript.model_validate(k788)
    continuity.log_cast(studio, sc, "K0788")
    raw = copy.deepcopy(k788)
    raw["kural_number"] = 1330
    raw["cast"][0]["name_ta"] = "சரோ"
    warns = continuity._cast_repeats(studio, continuity.sheet(studio), EpisodeScript.model_validate(raw))
    assert any("name சரோ was used in K0788" in w for w in warns)
    assert any("voice Achird was used in K0788" in w for w in warns)


def test_voices_per_story(studio, k788):
    sc = EpisodeScript.model_validate(k788)
    assert voice.voice_for(studio, "vignesh", sc) == "Achird"
    assert voice.voice_for(studio, "narrator", sc) == "Charon"
    studio.raw["voice"]["provider"] = "google_tts"
    assert voice.voice_for(studio, "saro", sc) == "ta-IN-Chirp3-HD-Enceladus"
    # Flow is told how the character sounds, from the cast sheet
    clip = continuity.clip_prompt(studio, sc, sc.shots[5], 8)
    assert "husky, breathless 29-year-old" in clip and "calm, friendly" in clip


def test_clip_reuse_and_credit_cap(studio, k788):
    sc = EpisodeScript.model_validate(k788)
    ep = studio.root / "episodes/K0788"
    sheet = visuals.flow_sheet(studio, ep, sc, "K0788")
    images = [j["shot"] for j in sheet["jobs"] if j["kind"] == "image"]
    clips = {j["shot"]: j["seconds"] for j in sheet["jobs"] if j["kind"] == "clip"}
    assert 2 not in images and 9 not in images and 2 not in clips   # shots 2 and 9 cut from shot 1's clip
    assert clips[1] == 8                                              # long enough for the later cuts
    refs = [j["save_as"] for j in sheet["jobs"] if j["kind"] == "character_ref"]
    assert refs == ["episodes/K0788/refs/characters/appa.png", "episodes/K0788/refs/characters/saro.png",
                    "episodes/K0788/refs/characters/vignesh.png"]
    readme = (ep / "flow" / "README.md").read_text("utf-8")   # every shot has its entry, reused ones too
    assert "## Shot 2 (3–8 s): no new generation" in readme and "Uses seconds 3–8 of shot 1's clip" in readme
    assert "## Shot 9 (38–43 s): no new generation" in readme
    studio.raw["budget"]["per_reel_credits"] = 60
    assert visuals.credit_check(studio, sc) and "64 Flow credits" in visuals.credit_check(studio, sc)[0]
    raw = copy.deepcopy(k788)
    raw["shots"][8]["clip_offset_s"] = 4.0                           # 4 + 5 s runs past the 8 s clip
    assert any("past its 8 s end" in e for e in _checks(studio, raw)[0])


def test_reused_cut_starts_later_in_the_clip(studio, k788, tmp_path):
    sc = EpisodeScript.model_validate(k788)
    ep = tmp_path / "ep"
    (ep / "images").mkdir(parents=True)
    (ep / "clips").mkdir()
    studio.raw["images"]["provider"] = studio.raw["video"]["provider"] = "flow"
    for sh in sc.shots:
        if not sh.clip_from:
            (ep / "images" / f"shot{sh.n:02d}.png").write_bytes(b"x")
            (ep / "clips" / f"shot{sh.n:02d}.mp4").write_bytes(b"x")
    m = visuals.generate(studio, ep, sc, "K0788")
    by_n = {x["n"]: x for x in m["shots"]}
    assert by_n[2]["clip"] == by_n[9]["clip"] == "shot01.mp4" and by_n[9]["clip_from"] == 1
    assert 2 not in m["animated"] and 1 in m["animated"]


def test_dry_run_stub_uses_a_cast(studio):
    store = KuralStore(studio.path("kurals"))
    raw = scriptgen.dry_run_script(store.get(302))
    assert len(raw["cast"]) == 2 and _checks(studio, raw)[0] == []


def test_kids_special_and_prompt(studio):
    from orukural.kurals import kids_specials_per_month
    store = KuralStore(studio.path("kurals"))
    assert studio["kids_special"] == {"cast": "kumbakonam", "per_month": 1}
    studio.raw["lineup"].insert(3, {"kural": 302, "relationship": "family", "special": "kids"})
    assert kids_specials_per_month(studio["lineup"], 3)[0] == 1
    special = scriptgen.user_prompt(studio, store.get(302), None, [])
    assert "monthly kids' special" in special and "leave `cast` empty" in special
    normal = scriptgen.user_prompt(studio, store.get(788), None, [], [{"episode": "K0301", "cast": []}])
    assert "Relationship: friends" in normal and "thatha_cameo" in normal and "Recent casts" in normal
    system = scriptgen.system_prompt(studio)
    for must in ("Invent this story's own 2–3 characters", "aim for 7 clips", "Never name a posting day or time",
                 "towering over a child", "Save this", "tag"):
        assert must in system


def test_publish_pack_has_no_schedule_and_a_checklist(studio, k788):
    store = KuralStore(studio.path("kurals"))
    sc = EpisodeScript.model_validate(k788)
    text = publish.render(studio, store.get(788), sc)
    assert "🔔" not in text and "7:30" not in text
    assert "Add AI label switched ON before Share" in text and "uploaded as the thumbnail before Publish" in text
    assert "உங்க 3 AM நண்பனை tag பண்ணுங்க" in text
    sc.instagram.caption_ta += "\nNew kural every Mon, Wed & Sat"
    with pytest.raises(SystemExit, match="posting day or time"):
        publish.render(studio, store.get(788), sc)


def test_voice_source_review_choice(studio, k788, tmp_path):
    sc = EpisodeScript.model_validate(k788)
    assert lipsync.voice_sources(sc, {}) == {"vignesh": "tts", "saro": "tts", "appa": "tts"}   # default: ours
    assert lipsync.voice_sources(sc, {"voice_source": {"saro": "flow"}})["saro"] == "flow"


@ffmpeg
def test_voice_ab_preview_and_flow_voice(studio, k788, tmp_path):
    sc = EpisodeScript.model_validate(k788)
    ep = tmp_path / "ep"
    (ep / "voice").mkdir(parents=True)
    clip = tmp_path / "shot06.mp4"
    # a clip whose sound has two stretches of "speech" (tones) with silence between: Saro's line, then Vignesh's
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=720x1280:d=8", "-f", "lavfi",
                    "-i", "sine=f=300:d=8", "-filter_complex",
                    "[1:a]volume='if(between(t,1,3.5)+between(t,4.5,7.5),1,0)':eval=frame[a]", "-map", "0:v",
                    "-map", "[a]", "-shortest", "-pix_fmt", "yuv420p", str(clip)], check=True)
    for i in (6, 7):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=f=500:d=2",
                        str(ep / "voice" / f"seg{i:02d}_story.mp3")], check=True)
    made = lipsync.ab_preview(studio, ep, sc, {6: clip}, tmp_path / "review")
    assert sorted(p.name for p in made) == ["voice_ab_saro.m4a", "voice_ab_vignesh.m4a"]
    from orukural import media
    assert media.duration(made[0]) > 2.5 + 0.6 + 2.0       # Flow's line, a gap, then ours
    # choosing flow for Saro: his line plays from the clip, Vignesh's stays ours
    (ep / "lipsync.json").write_text(json.dumps({"voice_source": {"saro": "flow"}}))
    segs = [{"n": i + 1, "beat": g.beat, "speaker": g.speaker, "file": f"seg{i + 1:02d}_story.mp3",
             "start": g.start_s, "end": g.end_s, "voice_seconds": 2.0} for i, g in enumerate(sc.segments)]
    shots = [(sh, sh.start_s, sh.end_s) for sh in sc.shots]
    out, _, notes = lipsync.fit(studio, ep, sc, segs, shots, {6: clip})
    assert out[5]["lipsync"].get("voice") == "flow" and "voice" not in out[6]["lipsync"]


@ffmpeg
def test_signature_parts_and_previews(studio):
    from PIL import Image
    from orukural import media
    parts = signature.build(studio)
    assert set(parts) == {"flute_end", "ending"}            # no intro, no badge flick, no opening flute
    assert abs(media.duration(parts["ending"]) - 2.0) < 0.1
    store = KuralStore(studio.path("kurals"))
    made = signature.previews(studio, store.get(788), None, studio.root / "review" / "signature")
    assert [p.name for p in made] == ["signature_kural_A_slim_leaf.mp4", "signature_kural_A_slim_leaf.png",
                                      "signature_kural_B_clean_text.mp4", "signature_kural_B_clean_text.png",
                                      "signature_logo_ending.mp4"]
    assert abs(media.duration(made[0]) - 7.0) < 0.1          # subtitle, kural, lesson card
    leaf = Image.open(studio.root / "review/signature/slim_leaf/kural_leaf.png")
    assert leaf.width <= 0.9 * media.W and leaf.height <= 0.18 * media.H      # a strip, not a board
    assert leaf.getpixel((leaf.width // 2, 8))[3] < 255                        # see-through
    segs = [{"beat": "hook", "start": 0, "end": 3}, {"beat": "kural", "start": 25.4, "end": 34.0}]
    plan = signature.plan(studio, store.get(788), segs, 43.0, studio.root / "r")
    assert plan["kural"]["style"] == "clean_text" and plan["kural"]["start"] == 25.4   # the chosen style
    assert "badge" not in plan and "flute_hook" not in plan
    assert len(plan["kural"]["layers"]) == 2 and plan["kural"]["dim"] == 0.45
    assert any("colorchannelmixer" in c for c in signature.video_graph(plan, "w", 3)[1])
    # the verse block is centred on screen
    boxes = [Image.open(p).getbbox() for p in plan["kural"]["layers"]]
    left, top = min(b[0] for b in boxes), min(b[1] for b in boxes)
    right, bottom = max(b[2] for b in boxes), max(b[3] for b in boxes)
    assert abs((left + right) / 2 - media.W / 2) <= 1 and abs((top + bottom) / 2 - media.H / 2) <= 1
    # clear of the Shorts/Reels buttons (right edge, bottom quarter) and the logo badge over Flow's mark
    cover = studio["assembly"]["watermark_cover"]
    assert right <= media.W - 60 and bottom < media.H * 0.75 and bottom < cover["y"]
    studio.raw["signature"]["kural"]["style"] = "slim_leaf"
    plan = signature.plan(studio, store.get(788), segs, 43.0, studio.root / "r")
    ins, chain, _ = signature.video_graph(plan, "w", 3)
    assert ins.count("-i") == 2                              # the leaf and the ending
    studio.raw["signature"]["enabled"] = False
    assert signature.plan(studio, store.get(788), segs, 43.0, studio.root / "r") is None

def test_voice_picker_makes_no_api_calls(studio, k788, monkeypatch):
    def no_calls(*a, **k):
        raise AssertionError("the voice picker must not call any API")
    monkeypatch.setattr(voice.requests, "post", no_calls)
    monkeypatch.setattr(voice, "_gemini_client", no_calls)
    monkeypatch.setattr(voice, "synthesize", no_calls)
    raw = _without_appa(copy.deepcopy(k788))
    for c in raw["cast"]:
        c["voice"] = ""
    raw["cast"][0]["personality"] = "calm, friendly"
    raw["cast"].append({"id": "nila", "name_ta": "நிலா", "age": 7, "job": "school girl", "gender": "female",
                        "age_group": "child", "look_en": "x", "outfit_en": "y", "personality": "bright"})
    sc = EpisodeScript.model_validate(raw)
    picked = continuity.pick_voices(studio, sc)
    table = continuity.sheet(studio)["casting"]["voices"]
    assert set(picked) == {"vignesh", "saro", "nila"} and len(set(picked.values())) == 3
    assert table[picked["vignesh"]]["gender"] == "male" and not table[picked["vignesh"]].get("young")
    assert picked["vignesh"] == "Achird"                     # "friendly" matches its feel
    assert table[picked["saro"]]["gender"] == "male" and table[picked["nila"]].get("young")
    assert "Charon" not in picked.values()
    assert all(continuity.voice_mismatch(c, table) == [] for c in sc.cast)
    assert continuity.pick_voices(studio, sc) == {}            # already chosen: left alone


def test_tts_sends_only_the_words(studio, tmp_path, monkeypatch):
    """A style note before the words was read aloud, and the model refuses a system instruction: words only."""
    sent = []

    class Interactions:
        def create(self, **kw):
            sent.append(kw)
            raise RuntimeError("stop here")

    monkeypatch.setattr(voice, "_gemini_client", lambda *a: type("C", (), {"interactions": Interactions()})())
    with pytest.raises(RuntimeError):
        voice._gemini(studio, "Achird", "சாவியக் குடு.", tmp_path / "x.mp3", "calm")
    assert sent[0]["input"][0]["text"] == "சாவியக் குடு." and "system_instruction" not in sent[0]

def test_no_subtitles_while_the_kural_is_on_screen(studio, k788):
    from orukural import captions
    sc = EpisodeScript.model_validate(k788)
    segs = [{"start": g.start_s, "end": g.end_s, "voice_seconds": g.end_s - g.start_s - 0.5} for g in sc.segments]
    kural = next(g for g in sc.segments if g.beat == "kural")
    cues = captions.cues(studio, sc, segs, sc.segments[-1].end_s)
    assert cues and not any(a < kural.end_s and b > kural.start_s for _, a, b in cues)
    # with the slim leaf, it sits in the subtitle zone instead
    k = studio["signature"]["kural"]
    sub_y = 1920 - studio["captions"]["margin"]
    assert k["y"] < sub_y < k["y"] + k["height"] * 1920
    studio.raw["signature"]["enabled"] = False             # no kural reveal: the verse is subtitled as before
    cues = captions.cues(studio, sc, segs, sc.segments[-1].end_s)
    assert any(a < kural.end_s and b > kural.start_s for _, a, b in cues)


def test_an_elder_when_the_story_needs_one(studio, k788):
    sc = EpisodeScript.model_validate(k788)
    appa = next(c for c in sc.cast if c.id == "appa")
    assert appa.age_group == "elder" and _checks(studio, k788)[0] == []
    table = continuity.sheet(studio)["casting"]["voices"]
    assert table[appa.voice]["gender"] == "male" and table[appa.voice].get("older")   # an older-sounding voice
    assert "appa" in sc.shots[3].characters                  # shown in the auto, with no lines of his own
    assert not any(g.speaker == "appa" for g in sc.segments)
    raw = copy.deepcopy(k788)
    raw["cast"][2]["age"] = 40
    assert any("appa is 40 but age_group elder is 50–80" in e for e in _checks(studio, raw)[0])


def test_flow_progress_counts_saved_files(studio, k788):
    sc = EpisodeScript.model_validate(k788)
    ep = studio.root / "episodes/K0788"
    visuals.flow_sheet(studio, ep, sc, "K0788")
    before = visuals.progress(studio, ep)
    assert before["image"] == {"done": 0, "total": 7, "missing": [f"K0788_shot{n:02d}_image" for n in (1, 3, 4, 5, 6, 7, 8)]}
    (ep / "images").mkdir(parents=True)
    (ep / "images" / "shot01.jpeg").write_bytes(b"x")      # Flow's jpeg counts for the .png job
    (ep / "images" / "shot03.png").write_bytes(b"x")
    after = visuals.progress(studio, ep)
    assert after["image"]["done"] == 2 and "K0788_shot01_image" not in after["image"]["missing"]
    assert after["clip"]["done"] == 0 and after["clip"]["total"] == 7


def test_voice_lines_too_long_block_the_render(studio, k788):
    sc = EpisodeScript.model_validate(k788)
    need = voice.expected_seconds(studio, sc.segments[0].narration_ta)
    ok = {"segments": [{"n": 1, "seconds": need * 1.2}]}
    bad = {"segments": [{"n": 1, "seconds": need * 1.5 + 2.0}]}          # e.g. an English note read aloud first
    assert voice.too_long(studio, sc, ok) == []
    assert "line 1 (saro)" in voice.too_long(studio, sc, bad)[0]
