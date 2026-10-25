"""Phase 1: write the Tamil episode script, shot list and metadata with Claude."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
import yaml

from . import continuity
from .config import Settings
from .kurals import STATUSES, KuralStore, verse_text
from .ledger import Ledger
from .schema import EpisodeScript, check

# USD per million tokens. Check https://platform.claude.com/docs/en/about-claude/pricing when changing model.
PRICES = {
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.40, "cache_write": 5.00},
}
RECENT_EPISODES = 12


def episode_dir(s: Settings, kural: dict) -> Path:
    return s.path("episodes") / kural["id"]


def system_prompt(s: Settings) -> str:
    template = (s.root / "prompts" / "script_system.md").read_text("utf-8")
    return (template
            .replace("{lessons}", s.file("lessons_file").read_text("utf-8").strip())
            .replace("{characters}", s.file("characters_file").read_text("utf-8").strip()))


def recent_episodes(s: Settings, exclude: str) -> list[dict]:
    out = []
    for f in sorted(s.path("episodes").glob("K*/script.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.parent.name == exclude:
            continue
        d = json.loads(f.read_text("utf-8"))
        if d.get("dry_run"):
            continue
        sc = d["script"]
        out.append({
            "kural": sc["kural_number"],
            "title": sc["story_title_en"],
            "logline": sc["logline_en"],
            "hook": sc["hooks"][sc["chosen_hook"]]["on_screen_ta"],
            "lesson": sc["lesson_ta"],
        })
        if len(out) == RECENT_EPISODES:
            break
    return out


def user_prompt(s: Settings, kural: dict, nxt: dict | None, recent: list[dict]) -> str:
    adh = kural["adhikaram"]
    lines = [
        f"Write the episode for kural #{kural['number']}.",
        "",
        "Verse (use exactly):",
        verse_text(kural),
        "",
        f"Adhikaram {adh['number']}: {adh['name_ta']} ({adh['name_en']}), kural {adh['position']} of 10 in this chapter.",
        f"Paal: {kural['paal']['name_ta']} ({kural['paal']['name_en']}). Theme tag: {kural['theme']}.",
        f"Fixed hashtags: {' '.join(s['script']['fixed_hashtags'])}",
    ]
    if nxt:
        lines += ["", f"Next episode (for the tease, do not explain it): kural #{nxt['number']}, "
                      f"theme {nxt['theme']}:", verse_text(nxt)]
    if recent:
        lines += ["", "Recent episodes (do not repeat their premise, hook or lesson wording):",
                  yaml.safe_dump(recent, allow_unicode=True, sort_keys=False)]
    return "\n".join(lines)


def cost_of(usage, model: str) -> float:
    p = PRICES[model]
    return (
        (usage.input_tokens or 0) * p["input"]
        + (usage.output_tokens or 0) * p["output"]
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * p["cache_read"]
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * p["cache_write"]
    ) / 1_000_000


def call_claude(s: Settings, system: str, user: str) -> tuple[dict, float, dict]:
    cfg = s["script"]
    client = anthropic.Anthropic(timeout=600)
    kwargs = dict(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        thinking={"type": "adaptive"},
        output_config={"effort": cfg["effort"]},
        output_format=EpisodeScript,
    )
    if cfg.get("server_side_fallback", True):
        kwargs.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    response = client.beta.messages.parse(**kwargs)
    if response.stop_reason == "refusal":
        detail = response.stop_details.explanation if response.stop_details else ""
        raise RuntimeError(f"model declined the request: {detail}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("script was cut off at max_tokens; raise script.max_tokens in config.yaml")
    script = response.parsed_output
    if script is None:
        raise RuntimeError("model returned no parsable script")
    cost = cost_of(response.usage, response.model if response.model in PRICES else cfg["model"])
    extra = {
        "provider": "anthropic",
        "model": response.model,
        "request_id": response._request_id,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
    }
    return script.model_dump(), cost, extra


def dry_run_script(kural: dict) -> dict:
    """A structurally valid placeholder so later phases can be exercised without spending."""
    v = kural["verse"]
    n = kural["number"]
    beats = [("hook", 0, 3), ("story", 3, 25), ("kural", 25, 35), ("lesson", 35, 41), ("tease", 41, 43)]
    say = {"hook": "[DRY RUN] கேள்வி?", "story": "[DRY RUN] கதை.", "kural": f"{v['line1']} {v['line2']}",
           "lesson": "[DRY RUN] பாடம்.", "tease": "[DRY RUN] அடுத்த குறள்."}
    shots = [(1, "hook", 0, 3), (2, "story", 3, 8), (3, "story", 8, 14), (4, "story", 14, 20),
             (5, "story", 20, 25), (6, "kural", 25, 30), (7, "kural", 30, 35), (8, "lesson", 35, 43)]
    return EpisodeScript(
        kural_number=n, story_title_ta="[DRY RUN]", story_title_en="[DRY RUN]", logline_en="dry run",
        originality_note_en="dry run", meaning_ta="[DRY RUN]", meaning_en="[DRY RUN]",
        hooks=[{"style": st, "on_screen_ta": "[DRY RUN]", "narration_ta": "[DRY RUN] கேள்வி?"}
               for st in ("question", "tense_moment", "surprising_line")],
        chosen_hook=0,
        continuity={"locations": [{"id": "thatha_thinnai", "description_en": "", "light_en": "golden hour",
                                   "blocking_en": "Thatha in his chair on the right, Kavin on the left"}],
                    "props": [], "outfits": [{"character": "thatha", "outfit_en": "white veshti, cream shirt"},
                                             {"character": "kavin", "outfit_en": "orange rocket T-shirt"}]},
        segments=[{"beat": b, "start_s": a, "end_s": e, "speaker": "narrator", "narration_ta": say[b],
                   "on_screen_ta": ""} for b, a, e in beats],
        shots=[{"n": i, "beat": b, "start_s": a, "end_s": e, "characters": ["thatha", "kavin"],
                "location": "thatha_thinnai", "action_en": "placeholder", "camera_en": "medium shot",
                "image_prompt_en": "placeholder", "motion_prompt_en": "placeholder"} for i, b, a, e in shots],
        lesson_ta="[DRY RUN]", tease_ta="[DRY RUN]", loop_note_en="dry run",
        youtube={"title": f"குறள் {n} | [DRY RUN]", "description_intro_ta": "[DRY RUN]",
                 "tags": ["thirukkural"], "pinned_comment_ta": "[DRY RUN]"},
        instagram={"caption_ta": "[DRY RUN]", "hashtags": ["#திருக்குறள்", "#thirukkural", "#ஒருகுறள்ஒருகதை"]},
    ).model_dump()


def write_outputs(s: Settings, kural: dict, script: dict, meta: dict) -> tuple[list[str], list[str]]:
    d = episode_dir(s, kural)
    d.mkdir(parents=True, exist_ok=True)
    parsed = EpisodeScript.model_validate(script)
    errors, warns = check(parsed, kural, s.raw)
    c_err, c_warn = continuity.check(s, parsed)
    errors, warns = errors + c_err, warns + c_warn
    payload = {**meta, "kural_id": kural["id"], "errors": errors, "warnings": warns, "script": script}
    (d / "script.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", "utf-8")
    (d / "script.md").write_text(render_markdown(s, kural, parsed, errors, warns), "utf-8")
    (d / "youtube_description.txt").write_text(youtube_description(s, kural, parsed), "utf-8")
    return errors, warns


def generate(s: Settings, store: KuralStore, ref: int | str, force: bool = False) -> dict:
    kural = store.get(ref)
    nxt = store.after(kural, s["adhikaram_order"])
    system = system_prompt(s)
    user = user_prompt(s, kural, nxt, recent_episodes(s, kural["id"]))
    d = episode_dir(s, kural)
    d.mkdir(parents=True, exist_ok=True)
    (d / "script_prompt.md").write_text(f"# System\n\n{system}\n\n# User\n\n{user}\n", "utf-8")

    if s["script"]["provider"] == "session" and not s.dry_run:
        # Claude writes the script in the weekly session (no API spend), then runs script-check.
        schema = s.root / "prompts" / "episode_script.schema.json"
        schema.write_text(json.dumps(EpisodeScript.model_json_schema(), ensure_ascii=False, indent=1), "utf-8")
        return {"kural": kural, "dir": d, "errors": [], "warnings": [], "dry_run": False, "cost": 0.0,
                "session": True, "next": (
                    f"Write the episode as JSON matching prompts/episode_script.schema.json to "
                    f"{(d / 'script.json').relative_to(s.root)}, following {(d / 'script_prompt.md').relative_to(s.root)}; "
                    f"then run `python studio.py script-check {kural['number']}`.")}

    if s.dry_run:
        meta = {"dry_run": True, "model": None, "cost_usd": 0.0, "cached": False}
        errors, warns = write_outputs(s, kural, dry_run_script(kural), meta)
        return {"kural": kural, "dir": d, "errors": errors, "warnings": warns, "dry_run": True, "cost": 0.0}

    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Add it to .env, or run with --dry-run.")

    ledger = Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])
    res = ledger.run(
        episode_id=kural["id"], step="script",
        inputs={"model": s["script"]["model"], "effort": s["script"]["effort"], "system": system, "user": user},
        estimate_usd=s["budget"]["estimates"]["script_call"],
        call=lambda: call_claude(s, system, user),
        force=force,
    )
    meta = {"dry_run": False, "model": s["script"]["model"], "cost_usd": round(res.cost_usd, 4),
            "cached": res.cached, "cache_key": res.key}
    errors, warns = write_outputs(s, kural, res.value, meta)
    script = res.value
    if not errors:
        store.set(kural["number"], status="scripted", episode_id=kural["id"],
                  meaning_ta=script["meaning_ta"], meaning_en=script["meaning_en"])
        store.save()
    return {"kural": kural, "dir": d, "errors": errors, "warnings": warns, "dry_run": False,
            "cost": res.cost_usd, "cached": res.cached}


def revalidate(s: Settings, store: KuralStore, ref: int | str) -> dict:
    """Re-check a hand-edited script.json and refresh script.md / description."""
    kural = store.get(ref)
    d = episode_dir(s, kural)
    payload = json.loads((d / "script.json").read_text("utf-8"))
    if "script" not in payload:  # bare script written in a Claude session
        payload = {"dry_run": False, "model": "claude session", "cost_usd": 0.0, "cached": False, "script": payload}
    meta = {k: v for k, v in payload.items() if k not in {"script", "errors", "warnings", "kural_id"}}
    errors, warns = write_outputs(s, kural, payload["script"], meta)
    if not errors and not payload.get("dry_run"):
        sc = payload["script"]
        store.set(kural["number"], status=max(kural["status"], "scripted", key=_status_rank),
                  episode_id=kural["id"], meaning_ta=sc["meaning_ta"], meaning_en=sc["meaning_en"])
        store.save()
    return {"kural": kural, "dir": d, "errors": errors, "warnings": warns}


def _status_rank(status: str) -> int:
    return STATUSES.index(status)


# ---- human-readable outputs ---------------------------------------------------

def youtube_description(s: Settings, kural: dict, sc: EpisodeScript) -> str:
    links = s["monetization"]["links"]
    adh = kural["adhikaram"]
    tags = s["script"]["fixed_hashtags"] + [h for h in sc.instagram.hashtags if h not in s["script"]["fixed_hashtags"]]
    values = {
        "description_intro_ta": sc.youtube.description_intro_ta.strip(),
        "number_padded": f"{kural['number']:03d}",
        "verse_line1": kural["verse"]["line1"],
        "verse_line2": kural["verse"]["line2"],
        "meaning_ta": sc.meaning_ta,
        "meaning_en": sc.meaning_en,
        "adhikaram_number": adh["number"],
        "adhikaram_ta": adh["name_ta"],
        "adhikaram_en": adh["name_en"],
        "paal_ta": kural["paal"]["name_ta"],
        "longform_line": "",  # filled once the adhikaram compilation is published (phase 3/4)
        "link_in_bio": links["link_in_bio"],
        "ebook": links["ebook"],
        "merch": links["merch"],
        "hashtags": " ".join(tags[:5]),
    }
    text = (s.root / "prompts" / "youtube_description.md").read_text("utf-8").format(**values)
    # Drop lines whose link is still an unfilled {{PLACEHOLDER}} from config.yaml.
    kept = [ln for ln in text.splitlines() if "{" not in ln]
    return "\n".join(kept).replace("\n\n\n", "\n\n").strip() + "\n"


def render_markdown(s: Settings, kural: dict, sc: EpisodeScript, errors: list[str], warns: list[str]) -> str:
    adh = kural["adhikaram"]
    out = [
        f"# குறள் #{kural['number']:03d} · {sc.story_title_ta}",
        f"*{sc.story_title_en}* · அதிகாரம் {adh['number']}: {adh['name_ta']} ({adh['name_en']}) · "
        f"{kural['paal']['name_ta']} · runtime {sc.segments[-1].end_s:.0f} s",
        "",
        f"> {kural['verse']['line1']}  ",
        f"> {kural['verse']['line2']}",
        "",
        f"**பொருள் (our words):** {sc.meaning_ta}  ",
        f"**Meaning:** {sc.meaning_en}",
        "",
        f"**Logline:** {sc.logline_en}  ",
        f"**Why it's original:** {sc.originality_note_en}",
        "",
    ]
    if errors or warns:
        out += ["## Checks", ""] + [f"- ❌ {e}" for e in errors] + [f"- ⚠️ {w}" for w in warns] + [""]
    out += ["## Hooks", ""]
    for i, h in enumerate(sc.hooks):
        mark = " ← used" if i == sc.chosen_hook else ""
        out.append(f"{i + 1}. **{h.on_screen_ta}** ({h.style}){mark}  \n   🎙 {h.narration_ta}")
    out += ["", "## Script", "", "| Time | Beat | Who | Narration | On screen |", "|---|---|---|---|---|"]
    for seg in sc.segments:
        out.append(f"| {seg.start_s:g}–{seg.end_s:g} s | {seg.beat} | {seg.speaker} | "
                   f"{seg.narration_ta} | {(seg.on_screen_ta or '').replace(chr(10), '<br>')} |")
    out += ["", f"**Lesson:** {sc.lesson_ta}  ", f"**Tease:** {sc.tease_ta}  ", f"**Loop:** {sc.loop_note_en}",
            "", "## Continuity", ""]
    for loc in sc.continuity.locations:
        out.append(f"- **{loc.id}**: {loc.description_en} *Light:* {loc.light_en} *Blocking:* {loc.blocking_en}")
    for p in sc.continuity.props:
        out.append(f"- prop **{p.id}**" + (f" ({p.name_ta})" if p.name_ta else "") + f": {p.description_en}")
    for o in sc.continuity.outfits:
        out.append(f"- **{o.character}** wears {o.outfit_en}")
    out += ["", "## Shot list", ""]
    for sh in sc.shots:
        out += [
            f"**Shot {sh.n}** · {sh.start_s:g}–{sh.end_s:g} s · {sh.beat} · {', '.join(sh.characters)} · {sh.location}"
            + (f" · props: {', '.join(sh.props)}" if sh.props else "") + "  ",
            f"{sh.action_en} *Camera:* {sh.camera_en}  ",
            f"🖼 `{sh.image_prompt_en}`  ",
            f"🎞 `{sh.motion_prompt_en}`",
            "",
        ]
    out += [
        "## YouTube", "",
        f"**Title:** {sc.youtube.title}", "",
        "**Description:**", "", "```", youtube_description(s, kural, sc).rstrip(), "```", "",
        f"**Tags:** {', '.join(sc.youtube.tags)}", "",
        f"**Pinned comment:** {sc.youtube.pinned_comment_ta}", "",
        "## Instagram", "", sc.instagram.caption_ta, "", " ".join(sc.instagram.hashtags), "",
    ]
    return "\n".join(out)
