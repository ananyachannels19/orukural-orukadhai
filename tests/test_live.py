"""Studio Live: events, the state the dashboard reads, and the media whitelist."""

import json
import shutil
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from orukural import config, live

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def studio(tmp_path):
    for item in ("config.yaml", "data"):
        src = ROOT / item
        (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp_path / item)
    ep = tmp_path / "episodes" / "K0301"
    (ep / "images").mkdir(parents=True)
    shutil.copy(ROOT / "samples" / "K0301" / "script.json", ep / "script.json")
    (tmp_path / ".env").write_text("SECRET=1")
    return config.load(tmp_path / "config.yaml", dry_run=False)


def test_emit_never_raises_and_appends(studio, tmp_path):
    assert live.emit(studio, "K0301", "clips", "start", "Shot 2 clip", shot=2, attempt=1)["shot"] == 2
    live.emit(studio, "K0301", "clips", "done", "Shot 2 clip made", shot=2, credits=12, credits_left=231)
    (tmp_path / "logs" / "events.jsonl").open("a").write('{"half a line')
    assert [e["status"] for e in live.read_events(studio, "K0301")] == ["start", "done"]
    studio.root = tmp_path / "missing" / "\0bad"
    assert live.emit(studio, "K0301", "clips", "info") is None


def test_state_from_disk_and_events(studio, tmp_path):
    ep = tmp_path / "episodes" / "K0301"
    (ep / "images" / "shot01.png").write_bytes(b"png")
    (ep / "continuity_review.json").write_text(json.dumps({"images": {"1": "pass"}, "clips": {}}))
    live.emit(studio, "K0301", "clips", "blocked", "Flow unusual activity", shot=2)
    live.emit(studio, "K0301", "clips", "start", "Making shot 2", shot=2, attempt=3)
    live.emit(studio, "K0301", "clips", "info", "a note")
    st = live.state(studio)
    e = st["episode"]
    stages = {x["key"]: x for x in e["stages"]}
    assert stages["script"]["state"] == "done"
    assert (stages["images"]["done"], stages["images"]["total"]) == (1, 10)
    assert stages["image_check"]["done"] == 1
    assert stages["clips"]["state"] == "running"
    assert e["now"]["state"] == "running" and e["now"]["shot"] == 2   # the note does not hide it
    assert e["needs_you"] == []   # work went on after the block
    assert e["shots"][0]["image"].startswith("/media/episodes/K0301/images/shot01.png")
    assert e["shots"][1]["running"]
    assert st["budgets"]["tts"]["limit"] == 10
    assert any(d["kind"] == "post" for d in st["calendar"])


def test_server_serves_media_but_nothing_else(studio, tmp_path):
    (tmp_path / "episodes" / "K0301" / "images" / "shot01.png").write_bytes(b"0123456789")
    server = ThreadingHTTPServer(("127.0.0.1", 0), live.make_handler(studio))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert b"Studio Live" in urllib.request.urlopen(base + "/").read()
        assert json.loads(urllib.request.urlopen(base + "/api/state").read())["episode"]["id"] == "K0301"
        req = urllib.request.Request(base + "/media/episodes/K0301/images/shot01.png", headers={"Range": "bytes=2-4"})
        r = urllib.request.urlopen(req)
        assert r.status == 206 and r.read() == b"234"
        for bad in ("/media/.env", "/media/episodes/../.env", "/media/%2e%2e/config.yaml", "/media/config.yaml"):
            with pytest.raises(urllib.error.HTTPError):
                urllib.request.urlopen(base + bad)
    finally:
        server.shutdown()
