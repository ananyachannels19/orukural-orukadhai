import json
from pathlib import Path

import pytest

from orukural import config, scriptgen
from orukural.kurals import STATUSES, KuralStore
from orukural.ledger import BudgetExceeded, Ledger
from orukural.schema import EpisodeScript, check

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def settings():
    return config.load()


@pytest.fixture(scope="module")
def store(settings):
    return KuralStore(settings.path("kurals"))


def test_kurals_complete(store):
    assert [k["number"] for k in store.items] == list(range(1, 1331))
    for k in store.items:
        assert k["adhikaram"]["number"] == (k["number"] - 1) // 10 + 1
        assert k["status"] in STATUSES
        assert k["verse"]["line1"] and k["verse"]["line2"]
    assert {k["paal"]["number"] for k in store.items} == {1, 2, 3}
    assert len({k["adhikaram"]["name_ta"] for k in store.items}) >= 130


def test_no_commentary_copied(store):
    # Only our own meanings may appear; the source datasets' commentary fields must not.
    for k in store.items:
        assert set(k) >= {"meaning_ta", "meaning_en"}
        assert not {"mv", "sp", "mk", "explanation", "couplet"} & set(k)


def test_plan_follows_the_lineup(settings, store):
    lineup = [x["kural"] for x in settings["lineup"]]
    assert lineup == [788, 1330, 100, 467, 785, 1100, 190, 104]
    nxt = store.next_planned(settings["lineup"], 12)
    planned = [n for n in lineup if store.get(n)["status"] == "planned"]
    assert [k["number"] for k in nxt][:len(planned)] == planned
    assert store.after(store.get(788), settings["lineup"])["number"] == 1330
    # after the lineup, the rest in book order
    rest = [k["number"] for k in nxt[len(planned):]]
    assert rest == sorted(rest)


def test_relationship_tag(settings, store):
    import yaml
    from orukural.kurals import relationship
    themes = yaml.safe_load((ROOT / "data" / "themes.yaml").read_text("utf-8"))
    assert relationship(settings["lineup"], themes, store.get(1330)) == "couple"
    assert relationship(settings["lineup"], themes, store.get(790)) == "friends"   # adhikaram 79's default
    assert relationship(settings["lineup"], themes, store.get(1)) == "friends"     # nothing listed


def test_schedule_is_planning_only(settings):
    sched = settings["schedule"]
    assert sched["post_days"] == ["mon", "wed", "sat"] and sched["episodes_per_week"] == 3
    assert sched["post_time"] == "19:00"
    assert settings["budget"]["per_reel_credits"] == 75
    for f in ("prompts/youtube_description.md", "prompts/publish_post.md"):
        text = (ROOT / f).read_text("utf-8")
        assert "🔔" not in text and "7:30" not in text and "Mon, Wed" not in text


def test_sample_script_passes_checks(settings, store):
    payload = json.loads((ROOT / "samples" / "K0301" / "script.json").read_text("utf-8"))
    sc = EpisodeScript.model_validate(payload["script"])
    errors, _ = check(sc, store.get(301), settings.raw)
    assert errors == []


def test_check_catches_wrong_verse(settings, store):
    payload = json.loads((ROOT / "samples" / "K0301" / "script.json").read_text("utf-8"))
    payload["script"]["segments"][6]["narration_ta"] = "வேறு ஏதோ வரி"
    errors, _ = check(EpisodeScript.model_validate(payload["script"]), store.get(301), settings.raw)
    assert any("verse" in e for e in errors)


def test_dry_run_stub_is_valid(settings, store):
    sc = EpisodeScript.model_validate(scriptgen.dry_run_script(store.get(302)))
    errors, _ = check(sc, store.get(302), settings.raw)
    assert errors == []


def test_ledger_caches_and_caps(tmp_path):
    ledger = Ledger(tmp_path / "spend.jsonl", tmp_path / "cache", per_episode_cap=1.0)
    calls = []

    def paid():
        calls.append(1)
        return {"ok": True}, 0.6, {"model": "x"}

    a = ledger.run(episode_id="K1", step="script", inputs={"p": 1}, estimate_usd=0.1, call=paid)
    b = ledger.run(episode_id="K1", step="script", inputs={"p": 1}, estimate_usd=0.1, call=paid)
    assert (a.cached, b.cached, len(calls)) == (False, True, 1)
    assert ledger.spent("K1") == 0.6
    with pytest.raises(BudgetExceeded):
        ledger.run(episode_id="K1", step="image", inputs={"p": 2}, estimate_usd=0.5, call=paid)


def test_check_refuses_a_promised_schedule(settings, store):
    sc = EpisodeScript.model_validate(scriptgen.dry_run_script(store.get(302)))
    sc.instagram.caption_ta += "\n🔔 புதிய குறள்: திங்கள், புதன், சனி · 7:30 pm IST"
    errors, _ = check(sc, store.get(302), settings.raw)
    assert any("posting day or time" in e for e in errors)
    sc = EpisodeScript.model_validate(scriptgen.dry_run_script(store.get(302)))
    sc.tag_question_ta = "உங்க 3 AM நண்பனை tag பண்ணுங்க"   # an hour inside the story is fine
    assert check(sc, store.get(302), settings.raw)[0] == []


def test_new_format_checks(settings, store):
    raw = scriptgen.dry_run_script(store.get(302))
    raw["segments"][3]["speaker"] = "a"           # a character says the kural
    raw["segments"][-1]["on_screen_ta"] = "பாடம்"  # no "Save this" on the last card
    raw["segments"][2]["on_screen_ta"] = ""       # no lesson teaser at 10-12 s
    raw["tag_question_ta"] = ""
    raw["shots"][4]["clip_from"] = 6              # a later shot
    errors, warns = check(EpisodeScript.model_validate(raw), store.get(302), settings.raw)
    text = " | ".join(errors + warns)
    assert "narrator says the kural" in text and "Save this" in text and "teaser" in text
    assert "tag question" in text and "shot 5: clip_from" in text
