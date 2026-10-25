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


def test_plan_finishes_adhikaram_first(settings, store):
    order = store.adhikaram_sequence(settings["adhikaram_order"])
    nxt = store.next_planned(settings["adhikaram_order"], 25)
    ranks = [order.index(k["adhikaram"]["number"]) for k in nxt]
    assert ranks == sorted(ranks)
    assert len(set(ranks)) >= 2


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
