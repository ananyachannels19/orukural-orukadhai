"""Keeping characters, places, props and dialogue the same across an episode (and the series).

Three layers:
  1. The bible. `data/characters.yaml` fixes the world, the casting rules and the optional series
     casts; each script brings its own `cast` (2-3 new adults) and a `continuity` block (this
     episode's locations with light and blocking, props, outfits). Every image and clip prompt is
     built from these, not restated by hand per shot, so a detail can't drift between shots.
  2. Reference images. Characters, recurring locations and the episode's props each get one
     reference image, attached to every shot that shows them.
  3. Checks. `check()` catches script-level breaks (unknown ids, missing outfits, a speaker who
     is never on screen, a prop named in dialogue but not shown). The visual review
     (`studio.py continuity-sheet N`, then `episodes/<id>/continuity_review.json`) catches the
     ones only eyes can see, and assembly refuses to render until every shot passes.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from . import lipsync, media
from .config import Settings
from .schema import EpisodeScript, Shot

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
CAMEO = "thatha"  # the one series character a new-cast story may show, as a grandfather on a video call
REVIEW_FILE = "continuity_review.json"


def sheet(s: Settings) -> dict:
    return yaml.safe_load(s.file("characters_file").read_text("utf-8"))


def series_cast(sh: dict) -> dict[str, dict]:
    """Characters of the optional series casts (e.g. kumbakonam), each tagged with its cast set."""
    return {cid: {**c, "cast_set": name} for name, cs in (sh.get("casts") or {}).items()
            for cid, c in (cs.get("characters") or {}).items()}


def series_locations(sh: dict) -> dict[str, dict]:
    """Places with a fixed look and a shared reference image, from the series casts."""
    out = dict(sh.get("locations") or {})
    for cs in (sh.get("casts") or {}).values():
        out.update(cs.get("locations") or {})
    return out


def cast(sh: dict, script: EpisodeScript | None = None) -> dict[str, dict]:
    """Every character id this episode can use: the series casts, then the episode's own cast."""
    out = series_cast(sh)
    for c in (script.cast if script else []):
        out[c.id] = {"name": c.id.replace("_", " ").title(), "name_ta": c.name_ta, "age": c.age, "job": c.job,
                     "look": c.look_en, "wardrobe": {"episode": c.outfit_en}, "voice": c.voice,
                     "voice_en": c.voice_en, "episode_cast": True}
    return out


def label(names: dict[str, dict], cid: str) -> str:
    """How prompts refer to a character: "Thatha", "Vignesh"."""
    return names.get(cid, {}).get("name", cid.replace("_", " ").title()).split(" (")[0]


def flow_voice(s: Settings, names: dict[str, dict], cid: str) -> str:
    """How a character sounds, in words, so Flow picks a similar voice in every clip they speak in."""
    c = names.get(cid, {})
    if c.get("voice_en"):
        return c["voice_en"]
    if c.get("episode_cast"):
        return f"the natural voice of a {c['age']}-year-old Tamil {c['job']}"
    return (s["voice"].get("flow_voices") or {}).get(cid, "")


def _find(stem: Path) -> Path | None:
    for ext in IMAGE_EXT:
        if stem.with_suffix(ext).exists():
            return stem.with_suffix(ext)
    return None


# ---- reference images --------------------------------------------------------------

def ref_dirs(s: Settings, ep_dir: Path) -> dict[str, Path]:
    root = s.path("cache") / "dry_run_refs" if s.dry_run else s.root
    return {
        "character": root / s["images"]["characters_dir"],
        "location": root / s["continuity"]["locations_dir"],
        "episode_location": ep_dir / "refs" / "locations",
        "episode_character": ep_dir / "refs" / "characters",
        "prop": ep_dir / "refs" / "props",
    }


def location_ref_stem(s: Settings, ep_dir: Path, loc_id: str) -> Path:
    d = ref_dirs(s, ep_dir)
    series = loc_id in series_locations(sheet(s))
    return (d["location"] if series else d["episode_location"]) / loc_id


def character_ref_stem(s: Settings, ep_dir: Path, names: dict[str, dict], cid: str) -> Path:
    """Series characters share one reference image; an episode's own cast keeps theirs in the episode."""
    d = ref_dirs(s, ep_dir)
    return (d["episode_character"] if names.get(cid, {}).get("episode_cast") else d["character"]) / cid


def shot_refs(s: Settings, ep_dir: Path, script: EpisodeScript, shot: Shot) -> list[tuple[str, Path]]:
    """(label, path) of the reference images for one shot: characters, then the place, then props.
    Paths may not exist yet (Flow makes them from the job sheet)."""
    d = ref_dirs(s, ep_dir)
    names = cast(sheet(s), script)
    refs: list[tuple[str, Path]] = []
    for c in shot.characters:
        if c in names:
            stem = character_ref_stem(s, ep_dir, names, c)
            refs.append((label(names, c), _find(stem) or stem.with_suffix(".png")))
    stem = location_ref_stem(s, ep_dir, shot.location)
    refs.append((f"the place ({shot.location})", _find(stem) or stem.with_suffix(".png")))
    for p in shot.props:
        refs.append((f"the {p.replace('_', ' ')}", _find(d["prop"] / p) or d["prop"] / f"{p}.png"))
    return refs[: s["continuity"]["max_refs_per_image"]]


def location_text(s: Settings, script: EpisodeScript, loc_id: str) -> str:
    loc = next(x for x in script.continuity.locations if x.id == loc_id)
    series = series_locations(sheet(s)).get(loc_id)
    base = " ".join(series["description"].split()) if series else loc.description_en.strip()
    extra = f" Today: {loc.description_en.strip()}" if series and loc.description_en.strip() else ""
    return f"{base}{extra} Light: {loc.light_en.strip()} Staging: {loc.blocking_en.strip()}"


def character_ref_prompt(s: Settings, cid: str, script: EpisodeScript | None = None) -> str:
    sh = sheet(s)
    c = cast(sh, script)[cid]
    if c.get("episode_cast"):
        who = f"{c['name']}, a {c['age']}-year-old Tamil {c['job']}."
    else:
        who = f"{c.get('name', cid)}, {c['age']} years old." if "age" in c else f"{cid.replace('_', ' ').title()}."
    manner = f" A hint of their personality: {' '.join(c['voice_and_manner'].split())}" if "voice_and_manner" in c else ""
    wear = next(iter((c.get("wardrobe") or {}).values()), "")
    return (f"Character reference sheet for an animated series. {who} {' '.join(str(c['look']).split())} {wear} "
            f"Show the same character twice side by side: full body standing front view, and a head-and-shoulders "
            f"close-up. Neutral expression.{manner} Plain light warm-grey background. "
            f"Style: {' '.join(sh['world']['visual_style'].split())}")


def location_ref_prompt(s: Settings, script: EpisodeScript | None, loc_id: str) -> str:
    sh = sheet(s)
    series = series_locations(sh).get(loc_id)
    if series:
        desc = " ".join(series["description"].split())
        light = "Soft late-afternoon light."
    else:
        loc = next(x for x in script.continuity.locations if x.id == loc_id)
        desc, light = loc.description_en.strip(), loc.light_en.strip()
    return (f"Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. "
            f"{desc} {light} Style: {' '.join(sh['world']['visual_style'].split())}")


def prop_ref_prompt(s: Settings, script: EpisodeScript, prop_id: str) -> str:
    p = next(x for x in script.continuity.props if x.id == prop_id)
    return (f"Prop reference for an animated series: {p.description_en.strip()} Shown alone, whole, centred, "
            f"three-quarter view on a plain light warm-grey background. Style: "
            f"{' '.join(sheet(s)['world']['visual_style'].split())}")


def ref_jobs(s: Settings, ep_dir: Path, script: EpisodeScript, rel) -> list[dict]:
    """Flow jobs for character, location and prop references that don't exist yet."""
    jobs = []
    model = s["flow"]["image_model"]
    names = cast(sheet(s), script)
    for cid in sorted({c for x in script.shots for c in x.characters}):
        stem = character_ref_stem(s, ep_dir, names, cid)
        if cid in names and not _find(stem):
            jobs.append({"kind": "character_ref", "id": cid, "save_as": rel(stem.with_suffix(".png")),
                         "aspect_ratio": "1:1", "model": model, "prompt": character_ref_prompt(s, cid, script)})
    for loc in script.continuity.locations:
        stem = location_ref_stem(s, ep_dir, loc.id)
        if not _find(stem):
            jobs.append({"kind": "location_ref", "id": loc.id, "save_as": rel(stem.with_suffix(".png")),
                         "aspect_ratio": "9:16", "model": model, "prompt": location_ref_prompt(s, script, loc.id)})
    for p in script.continuity.props:
        stem = ref_dirs(s, ep_dir)["prop"] / p.id
        if not _find(stem):
            jobs.append({"kind": "prop_ref", "id": p.id, "save_as": rel(stem.with_suffix(".png")),
                         "aspect_ratio": "1:1", "model": model, "prompt": prop_ref_prompt(s, script, p.id)})
    return jobs


# ---- prompts built from the bible ---------------------------------------------------

def image_prompt(s: Settings, script: EpisodeScript, shot: Shot, ref_labels: list[str]) -> str:
    sh = sheet(s)
    names = cast(sh, script)
    outfits = {o.character: o.outfit_en.strip() for o in script.continuity.outfits}
    props = {p.id: p for p in script.continuity.props}
    parts = [f"Vertical 9:16 frame. Style: {' '.join(sh['world']['visual_style'].split())}",
             f"Place: {location_text(s, script, shot.location)}"]
    for c in shot.characters:
        info = names.get(c, {})
        look = " ".join(str(info.get("look", "")).split())
        wear = outfits.get(c) or next(iter((info.get("wardrobe") or {}).values()), "as on the character sheet")
        parts.append(f"{label(names, c)}: {look} Wearing (same in every shot): {wear.rstrip('.')}.")
        if c == CAMEO and script.cast and script.thatha_cameo:
            parts.append(f"{label(names, c)} is seen only on a phone or laptop screen in the shot, on a video call "
                         f"from his own home; he is not in the room.")
    for pid in shot.props:
        parts.append(f"Prop, {pid.replace('_', ' ')}: {props[pid].description_en.strip()}")
    parts.append(f"Shot: {shot.image_prompt_en.strip()} Camera: {shot.camera_en.strip()}")
    if ref_labels:
        listed = "; ".join(f"image {i + 1} is {lab}" for i, lab in enumerate(ref_labels))
        parts.append(f"Reference images: {listed}. Match faces, hair, glasses, body, clothes, the place and every "
                     f"prop exactly as in them; do not copy their layout or background.")
    parts.append("No text, letters, logos or subtitles anywhere in the image.")
    return "\n".join(parts)


def speech_direction(s: Settings, script: EpisodeScript, shot: Shot) -> str:
    """Who talks during this shot, and when, so mouths match the voice track laid over it later.

    A clip is made with no sound, so without this a model moves whichever mouth it likes: a listener in
    close-up "says" someone else's line, or the speaker sits silent while their voice plays."""
    names = cast(sheet(s), script)
    name = lambda c: label(names, c)  # noqa: E731
    lines, spoken = [], lipsync.spoken_lines(script, shot)
    for i, seg in enumerate(script.segments):
        a, b = max(seg.start_s, shot.start_s), min(seg.end_s, shot.end_s)
        if b - a < 0.5:
            continue
        a, b = a - shot.start_s, b - shot.start_s
        if i in spoken:
            # Flow says the real words, so lips, jaw, breath and gesture follow them; our voice replaces its
            # voice later, laid exactly where Flow's speech is (see lipsync.py)
            others = [name(c) for c in shot.characters if c != seg.speaker]
            verb = "keeps their mouth closed and listens" if len(others) == 1 else "keep their mouths closed and listen"
            rest = f" Meanwhile {' and '.join(others)} {verb}." if others else ""
            voice = flow_voice(s, names, seg.speaker)
            sound = f" in {voice.rstrip('.')}" if voice else ""
            lines.append(f"From about {max(a, 0.5):.1f} s, {name(seg.speaker)} says this line aloud{sound}, "
                         f"pronouncing every word exactly in clear standard Tamil, lips and jaw matching every "
                         f"word, the body acting it out, face in view while speaking: "
                         f"\"{seg.narration_ta.strip()}\"{rest}")
        elif seg.speaker in shot.characters:
            others = [name(c) for c in shot.characters if c != seg.speaker]
            verb = "keeps their mouth closed and listens" if len(others) == 1 else "keep their mouths closed and listen"
            rest = f" {' and '.join(others)} {verb}." if others else ""
            lines.append(f"From {a:.0f} s to {b:.0f} s {name(seg.speaker)} is talking: lips and jaw move clearly "
                         f"as if speaking, with small natural gestures.{rest}")
        else:
            lines.append(f"From {a:.0f} s to {b:.0f} s nobody on screen talks: every mouth stays closed.")
    return " ".join(lines) or "Nobody on screen talks: every mouth stays closed."


def someone_talks(s: Settings, script: EpisodeScript, shot: Shot) -> bool:
    """A speaker is on screen for at least half a second of their line: Flow then tends to invent a voice."""
    return any(seg.speaker in shot.characters and min(seg.end_s, shot.end_s) - max(seg.start_s, shot.start_s) >= 0.5
               for seg in script.segments)


def clip_prompt(s: Settings, script: EpisodeScript, shot: Shot, secs: int) -> str:
    return (f"{shot.motion_prompt_en.strip()} Camera: {shot.camera_en.strip()} About {secs} seconds, one continuous "
            f"shot, no cuts. {speech_direction(s, script, shot)} Keep every character's face, hair, clothes and "
            f"size, the place, the light and every object exactly as in the start frame; nothing appears, "
            f"disappears or changes colour. No on-screen text. {_sound(script, shot)}")


def _sound(script: EpisodeScript, shot: Shot) -> str:
    if lipsync.spoken_lines(script, shot):
        return ("Sound: only the spoken line(s) above and the natural sounds of the scene; no music, "
                "no other voices.")
    return ("Sound: only the natural sounds of the scene (footsteps, the puppy, birds, wind); no music, "
            "and no voice or speech is heard.")


# ---- script checks -----------------------------------------------------------------

def check(s: Settings, script: EpisodeScript) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    sh = sheet(s)
    names = cast(sh, script)
    bible = script.continuity
    loc_ids = [x.id for x in bible.locations]
    prop_ids = [x.id for x in bible.props]
    cast_ids = [c.id for c in script.cast]
    for kind, ids in (("location", loc_ids), ("prop", prop_ids), ("cast", cast_ids)):
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            errors.append(f"duplicate {kind} ids: {sorted(dup)}")

    on_screen = {c for shot in script.shots for c in shot.characters}
    cameo = {CAMEO} & on_screen if script.cast and script.thatha_cameo else set()
    if script.cast and CAMEO in on_screen and not script.thatha_cameo:
        errors.append("Thatha is in a new-cast story only as a video-call cameo: set thatha_cameo")
    series_here = {c for c in on_screen if names.get(c, {}).get("cast_set")} - cameo
    if script.cast and series_here:
        errors.append(f"series characters {sorted(series_here)} in a new-cast story (only Thatha's cameo is allowed)")
    unknown = on_screen - set(names)
    if unknown:
        errors.append(f"characters not in the episode's cast: {sorted(unknown)}")
    lo, hi = (sh.get("casting") or {}).get("per_episode", [2, 3])
    counted = on_screen - cameo
    if len(counted) > hi:
        errors.append(f"{len(counted)} characters on screen: {sorted(counted)}; keep to {lo}–{hi}")
    if script.cast:
        errors += _cast_errors(s, sh, script, on_screen, (lo, hi))
        warns += _cast_repeats(s, sh, script)
    dressed = {o.character for o in bible.outfits} | set(cast_ids) | cameo  # Thatha wears his wardrobe
    for c in sorted(on_screen - dressed - unknown):
        errors.append(f"no outfit in continuity for {c}")
    # who belongs to this story: its own cast, and any series cast it draws on
    sets = {names[c].get("cast_set") for c in on_screen - cameo if c in names} - {None}
    story = {cid for cid, c in names.items() if c.get("episode_cast") or c.get("cast_set") in sets} | cameo

    used_locs, used_props = set(), set()
    for shot in script.shots:
        if shot.location not in loc_ids:
            errors.append(f"shot {shot.n}: location {shot.location!r} is not in continuity.locations")
        used_locs.add(shot.location)
        for p in shot.props:
            if p not in prop_ids:
                errors.append(f"shot {shot.n}: prop {p!r} is not in continuity.props")
            used_props.add(p)
    for i in sorted(set(loc_ids) - used_locs):
        warns.append(f"location {i!r} is in the bible but no shot uses it")
    for i in sorted(set(prop_ids) - used_props):
        warns.append(f"prop {i!r} is in the bible but no shot shows it")
    if len(set(loc_ids)) > 3:
        warns.append(f"{len(set(loc_ids))} locations; keep to two or three")

    # Dialogue: a character who speaks should be seen during that line (or just before it),
    # and an object the dialogue names should be on screen around then.
    for seg in script.segments:
        near = [x for x in script.shots if x.start_s < seg.end_s and x.end_s > seg.start_s - 3]
        if seg.speaker != "narrator" and seg.speaker not in names:
            errors.append(f"{seg.start_s:g}–{seg.end_s:g}s: speaker {seg.speaker!r} is not in the cast")
        if seg.speaker in story and seg.beat != "hook":
            if not any(seg.speaker in x.characters for x in near):
                warns.append(f"{seg.start_s:g}–{seg.end_s:g}s: {seg.speaker} speaks but is not on screen")
        if seg.speaker in story:
            for x in script.shots:
                overlap = min(seg.end_s, x.end_s) - max(seg.start_s, x.start_s)
                if overlap >= 1.5 and x.characters and seg.speaker not in x.characters \
                        and all(c in story for c in x.characters):
                    warns.append(f"shot {x.n}: {seg.speaker} is heard for {overlap:.1f} s over a shot of "
                                 f"{', '.join(x.characters)} only; it will look like the wrong person is talking")
        for p in bible.props:
            if p.name_ta and p.name_ta in seg.narration_ta and not any(p.id in x.props for x in near):
                warns.append(f"{seg.start_s:g}–{seg.end_s:g}s: dialogue mentions {p.name_ta} ({p.id}) but no shot shows it")
        for cid in sorted(story - on_screen):
            name_ta = names[cid].get("name_ta", "")
            if name_ta and name_ta in seg.narration_ta:
                warns.append(f"{seg.start_s:g}–{seg.end_s:g}s: dialogue names {name_ta} ({cid}), who is never on screen")
    return errors, warns


def _cast_errors(s: Settings, sh: dict, script: EpisodeScript, on_screen: set[str], size: tuple[int, int]) -> list[str]:
    """The per-episode cast: 2-3 people, mostly adults 22-35, at most one child; each with their own voice,
    never the narrator's."""
    errors = []
    casting = sh.get("casting") or {}
    amin, amax = casting.get("age", [22, 35])
    ranges = {"adult": (amin, amax), "child": tuple(casting.get("child_age", [4, 15])),
              "elder": tuple(casting.get("elder_age", [50, 80]))}
    narrator = s["voice"]["gemini_tts"]["voice"]
    children = [c for c in script.cast if c.age_group == "child"]
    elders = [c for c in script.cast if c.age_group == "elder"]
    table = casting.get("voices") or {}
    for c in script.cast:
        lo, hi = ranges[c.age_group]
        if not lo <= c.age <= hi:
            errors.append(f"cast {c.id} is {c.age} but age_group {c.age_group} is {lo}–{hi}")
        errors += voice_mismatch(c, table)
        if c.voice == narrator:
            errors.append(f"cast {c.id} uses {narrator}, the narrator's voice")
    if len(children) > casting.get("max_children", 1):
        errors.append(f"{len(children)} children in the cast ({', '.join(c.id for c in children)}); at most "
                      f"{casting.get('max_children', 1)}, only when the story needs one")
    if len(elders) > casting.get("max_elders", 1):
        errors.append(f"{len(elders)} elders in the cast ({', '.join(c.id for c in elders)}); at most "
                      f"{casting.get('max_elders', 1)}, only when the story needs one")
    if len(children) >= len(script.cast) - len(children):
        errors.append("the cast is mostly adults: more adults than children")
    voices = [c.voice for c in script.cast]
    if len(set(voices)) < len(voices):
        errors.append(f"two characters share a voice: {voices}")
    episode = {c.id for c in script.cast} & on_screen
    if len(episode) < size[0]:
        errors.append(f"{len(episode)} of the episode's own characters on screen; cast {size[0]}–{size[1]}")
    return errors


def voice_mismatch(c, table: dict) -> list[str]:
    """A voice that doesn't fit the character: a woman's voice for a man, or a grown-up voice for a child."""
    v = table.get(c.voice)
    if v is None:
        return [f"cast {c.id}: voice {c.voice} is not in casting.voices"]
    if c.age_group == "child":
        return [] if v.get("young") else [f"cast {c.id} is a child: pick one of the young voices "
                                          f"({', '.join(k for k, x in table.items() if x.get('young'))}), not {c.voice}"]
    if v["gender"] != c.gender:
        return [f"cast {c.id} is {c.gender} but {c.voice} is a {v['gender']} voice"]
    return []


def pick_voices(s: Settings, script: EpisodeScript) -> dict[str, str]:
    """Give every cast member without a voice one from casting.voices: their gender (a young voice for a child),
    a feel matching their personality, never the narrator's, not used by the others or the recent casts.
    Reads the table only; no voice is synthesised to choose."""
    sh = sheet(s)
    casting = sh.get("casting") or {}
    table = casting.get("voices") or {}
    narrator = s["voice"]["gemini_tts"]["voice"]
    me = f"K{script.kural_number:04d}"
    recent = [e for e in cast_log(s) if e.get("episode") != me][-casting.get("no_repeat_episodes", 12):]
    taken = {c.get("voice") for e in recent for c in e.get("characters") or []}
    used = {c.voice for c in script.cast if c.voice} | {narrator}
    picked = {}
    for c in script.cast:
        if c.voice:
            continue
        fits = [(name, v) for name, v in table.items() if name not in used
                and (v.get("young") if c.age_group == "child" else v["gender"] == c.gender and not v.get("young"))]
        words = set(c.personality.lower().replace(",", " ").split())

        def score(item):
            name, v = item
            older = bool(v.get("older"))
            return (name not in taken, len(words & set(v["feel"].split("-")) | words & {v["feel"]}),
                    older if c.age_group == "elder" else not older)
        if not fits:
            continue
        name = max(fits, key=score)[0]  # max keeps the table's order among equals, so the pick is stable
        c.voice = picked[c.id] = name
        used.add(name)
    return picked


def cast_log(s: Settings) -> list[dict]:
    f = s.root / "data" / "cast_log.yaml"
    return (yaml.safe_load(f.read_text("utf-8")) or {}).get("episodes") or [] if f.exists() else []


def _cast_repeats(s: Settings, sh: dict, script: EpisodeScript) -> list[str]:
    """Names and voices from recent episodes (data/cast_log.yaml) reused in this one."""
    me = f"K{script.kural_number:04d}"
    recent = [e for e in cast_log(s) if e.get("episode") != me][-(sh.get("casting") or {}).get("no_repeat_episodes", 12):]
    seen = {}
    for e in recent:
        for c in e.get("characters") or []:
            seen.setdefault(("name", c.get("name_ta")), e["episode"])
            seen.setdefault(("voice", c.get("voice")), e["episode"])
    out = []
    for c in script.cast:
        for kind, val in (("name", c.name_ta), ("voice", c.voice)):
            if (kind, val) in seen:
                out.append(f"cast {c.id}: {kind} {val} was used in {seen[(kind, val)]}; pick another")
    return out


def log_cast(s: Settings, script: EpisodeScript, episode_id: str) -> None:
    """Record (or refresh) this episode's cast in data/cast_log.yaml."""
    if not script.cast:
        return
    f = s.root / "data" / "cast_log.yaml"
    head = f.read_text("utf-8").split("episodes:")[0] if f.exists() else "# Who each episode cast.\n"
    entries = [e for e in cast_log(s) if e.get("episode") != episode_id]
    entries.append({"episode": episode_id,
                    "characters": [{"id": c.id, "name_ta": c.name_ta, "age": c.age, "job": c.job,
                                    "look": c.look_en, "voice": c.voice} for c in script.cast],
                    "places": [x.id for x in script.continuity.locations]}
                   | ({"cameo": CAMEO} if script.thatha_cameo else {}))
    f.write_text(head + yaml.safe_dump({"episodes": entries}, allow_unicode=True, sort_keys=False, width=120), "utf-8")


# ---- visual review -----------------------------------------------------------------

def load_review(ep_dir: Path) -> dict:
    f = ep_dir / REVIEW_FILE
    return json.loads(f.read_text("utf-8")) if f.exists() else {"images": {}, "clips": {}}


def review_gaps(script: EpisodeScript, review: dict, kind: str, shots: list[int] | None = None) -> list[str]:
    """Shots whose image or clip has not been marked 'pass' in the review file."""
    out = []
    for shot in script.shots:
        if shots is not None and shot.n not in shots:
            continue
        verdict = str(review.get(kind, {}).get(str(shot.n), "")).strip()
        if verdict.lower() != "pass":
            out.append(f"shot {shot.n}: {verdict or 'not reviewed'}")
    return out


def contact_sheet(s: Settings, ep_dir: Path, script: EpisodeScript, out_dir: Path) -> list[Path]:
    """Grids for the visual review: all shot images in order with the references beside them,
    and first / middle / last frames of every clip, so drift within a clip is visible."""
    from PIL import Image, ImageDraw

    out_dir.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []

    def grid(cells: list[tuple[str, Path]], cols: int, cell_w: int, name: str) -> Path | None:
        cells = [(lab, p) for lab, p in cells if p and p.exists()]
        if not cells:
            return None
        ims = []
        for lab, p in cells:
            im = Image.open(p).convert("RGB")
            im.thumbnail((cell_w, cell_w * 2))
            ims.append((lab, im))
        cell_h = max(im.height for _, im in ims) + 40
        rows = -(-len(ims) // cols)
        sheet_im = Image.new("RGB", (cols * (cell_w + 10) + 10, rows * (cell_h + 10) + 10), (32, 32, 32))
        d = ImageDraw.Draw(sheet_im)
        for k, (lab, im) in enumerate(ims):
            x, y = 10 + (k % cols) * (cell_w + 10), 10 + (k // cols) * (cell_h + 10)
            sheet_im.paste(im, (x, y + 36))
            d.text((x + 4, y + 8), lab[:64], fill=(255, 255, 255))
        path = out_dir / name
        sheet_im.save(path, quality=88)
        return path

    refs: dict[str, Path] = {}
    for shot in script.shots:
        for lab, p in shot_refs(s, ep_dir, script, shot):
            refs.setdefault(lab, p)
    r = grid(sorted(refs.items()), 6, 260, "references.jpg")
    images = [(f"shot {x.n} · {x.location} · {', '.join(x.characters + x.props)}",
               _find(ep_dir / "images" / f"shot{x.n:02d}")) for x in script.shots]
    i = grid(images, 5, 300, "images.jpg")
    frames = []
    fdir = out_dir / "frames"
    fdir.mkdir(exist_ok=True)
    for x in script.shots:
        clip = ep_dir / "clips" / f"shot{x.n:02d}.mp4"
        if not clip.exists():
            continue
        dur = media.duration(clip)
        for tag, t in (("first", 0.0), ("mid", dur / 2), ("last", max(0.0, dur - 0.1))):
            f = fdir / f"shot{x.n:02d}_{tag}.jpg"
            media.run(["-ss", f"{t:.2f}", "-i", str(clip), "-frames:v", "1", "-q:v", "3", str(f)])
            frames.append((f"shot {x.n} {tag}", f))
    c = grid(frames, 6, 220, "clip_frames.jpg")
    made = [p for p in (r, i, c) if p]
    review_file = ep_dir / REVIEW_FILE
    if not review_file.exists():
        blank = {"images": {str(x.n): "" for x in script.shots}, "clips": {str(x.n): "" for x in script.shots},
                 "notes": "Mark each shot 'pass', or write what is wrong (it will be redone)."}
        review_file.write_text(json.dumps(blank, indent=1), "utf-8")
    return made
