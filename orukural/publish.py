"""The posting package: everything to paste into YouTube Studio and Instagram, plus the checklist.

`studio.py publish-pack N` fills prompts/publish_post.md into episodes/<id>/publish/<id>_post.md.
Nothing here names a posting day or time; the schedule in config.yaml is for planning only."""

from __future__ import annotations

from pathlib import Path

from .config import Settings
from .schema import EpisodeScript, SCHEDULE_WORDS
from .scriptgen import youtube_description


def render(s: Settings, kural: dict, sc: EpisodeScript, video: str = "") -> str:
    tags = s["script"]["fixed_hashtags"] + [h for h in sc.instagram.hashtags if h not in s["script"]["fixed_hashtags"]]
    values = {
        "episode_id": kural["id"],
        "video": video or f"render/{kural['id']}_final.mp4",
        "title": sc.youtube.title,
        "title_chars": len(sc.youtube.title),
        "description": youtube_description(s, kural, sc).rstrip(),
        "tags": ", ".join(sc.youtube.tags),
        "pinned_comment": sc.youtube.pinned_comment_ta,
        "caption": sc.instagram.caption_ta.strip(),
        "tag_question": sc.tag_question_ta.strip(),
        "hashtags": " ".join(tags[:5]),
    }
    text = (s.root / "prompts" / "publish_post.md").read_text("utf-8").format(**values)
    # the last checklist line names days/times on purpose; check everything above it
    body = text.split("## Checklist")[0]
    lines = [ln for ln in body.splitlines() if SCHEDULE_WORDS.search(ln) and not ln.startswith("Video:")]
    if lines:
        raise SystemExit("the posting package names a posting day or time: " + " | ".join(lines))
    return text.replace("\n\n\n", "\n\n")


def write(s: Settings, kural: dict, sc: EpisodeScript, ep_dir: Path, video: str = "") -> Path:
    out = ep_dir / "publish" / f"{kural['id']}_post.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(s, kural, sc, video), "utf-8")
    return out
