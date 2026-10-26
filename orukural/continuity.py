"""Keeping characters, places, props and dialogue the same across an episode (and the series).

Three layers:
  1. The bible. `data/characters.yaml` fixes the cast, recurring locations and how people
     address each other; each script adds a `continuity` block (this episode's locations with
     light and blocking, props, outfits). Every image and clip prompt is built from these, not
     restated by hand per shot, so a detail can't drift between shots.
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

from . import media
from .config import Settings
from .schema import EpisodeScript, Shot

MAIN_CHARACTERS = ("thatha", "kavin")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
REVIEW_FILE = "continuity_review.json"


def sheet(s: Settings) -> dict:
    return yaml.safe_load(s.file("characters_file").read_text("utf-8"))


def cast(sh: dict) -> dict[str, dict]:
    """Every character id the series knows, with name_ta and look."""
    out = {cid: c for cid, c in sh["characters"].items() if cid != "supporting"}
    for c in sh["characters"].get("supporting", []):
        out[c["id"]] = c
    return out


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
        "prop": ep_dir / "refs" / "props",
    }


def location_ref_stem(s: Settings, ep_dir: Path, loc_id: str) -> Path:
    d = ref_dirs(s, ep_dir)
    series = loc_id in (sheet(s).get("locations") or {})
    return (d["location"] if series else d["episode_location"]) / loc_id


def shot_refs(s: Settings, ep_dir: Path, script: EpisodeScript, shot: Shot) -> list[tuple[str, Path]]:
    """(label, path) of the reference images for one shot: characters, then the place, then props.
    Paths may not exist yet (Flow makes them from the job sheet)."""
    d = ref_dirs(s, ep_dir)
    names = cast(sheet(s))
    refs: list[tuple[str, Path]] = []
    for c in shot.characters:
        if c in names:
            label = names[c].get("name", c).split(" (")[0] if c in MAIN_CHARACTERS else c.replace("_", " ")
            refs.append((label, _find(d["character"] / c) or d["character"] / f"{c}.png"))
    stem = location_ref_stem(s, ep_dir, shot.location)
    refs.append((f"the place ({shot.location})", _find(stem) or stem.with_suffix(".png")))
    for p in shot.props:
        refs.append((f"the {p.replace('_', ' ')}", _find(d["prop"] / p) or d["prop"] / f"{p}.png"))
    return refs[: s["continuity"]["max_refs_per_image"]]


def location_text(s: Settings, script: EpisodeScript, loc_id: str) -> str:
    loc = next(x for x in script.continuity.locations if x.id == loc_id)
    series = (sheet(s).get("locations") or {}).get(loc_id)
    base = " ".join(series["description"].split()) if series else loc.description_en.strip()
    extra = f" Today: {loc.description_en.strip()}" if series and loc.description_en.strip() else ""
    return f"{base}{extra} Light: {loc.light_en.strip()} Staging: {loc.blocking_en.strip()}"


def character_ref_prompt(s: Settings, cid: str) -> str:
    sh = sheet(s)
    c = cast(sh)[cid]
    who = f"{c.get('name', cid)}, {c['age']} years old." if "age" in c else f"{cid.replace('_', ' ').title()}."
    manner = f" A hint of their personality: {' '.join(c['voice_and_manner'].split())}" if "voice_and_manner" in c else ""
    wear = next(iter((c.get("wardrobe") or {}).values()), "")
    return (f"Character reference sheet for an animated series. {who} {' '.join(str(c['look']).split())} {wear} "
            f"Show the same character twice side by side: full body standing front view, and a head-and-shoulders "
            f"close-up. Neutral expression.{manner} Plain light warm-grey background. "
            f"Style: {' '.join(sh['world']['visual_style'].split())}")


def location_ref_prompt(s: Settings, script: EpisodeScript | None, loc_id: str) -> str:
    sh = sheet(s)
    series = (sh.get("locations") or {}).get(loc_id)
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
    cdir = ref_dirs(s, ep_dir)["character"]
    for cid in sorted({c for x in script.shots for c in x.characters} | set(MAIN_CHARACTERS)):
        if cid in cast(sheet(s)) and not _find(cdir / cid):
            jobs.append({"kind": "character_ref", "id": cid, "save_as": rel(cdir / f"{cid}.png"), "aspect_ratio": "1:1",
                         "model": model, "prompt": character_ref_prompt(s, cid)})
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
    names = cast(sh)
    outfits = {o.character: o.outfit_en.strip() for o in script.continuity.outfits}
    props = {p.id: p for p in script.continuity.props}
    parts = [f"Vertical 9:16 frame. Style: {' '.join(sh['world']['visual_style'].split())}",
             f"Place: {location_text(s, script, shot.location)}"]
    for c in shot.characters:
        info = names.get(c, {})
        look = " ".join(str(info.get("look", "")).split())
        wear = outfits.get(c) or next(iter((info.get("wardrobe") or {}).values()), "as on the character sheet")
        parts.append(f"{info.get('name', c)}: {look} Wearing (same in every shot): {wear.rstrip('.')}.")
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
    names = cast(sheet(s))
    label = lambda c: names.get(c, {}).get("name", c).split(" (")[0] if c in names else c.replace("_", " ")
    lines = []
    for seg in script.segments:
        a, b = max(seg.start_s, shot.start_s), min(seg.end_s, shot.end_s)
        if b - a < 0.5:
            continue
        a, b = a - shot.start_s, b - shot.start_s
        if seg.speaker in shot.characters:
            others = [label(c) for c in shot.characters if c != seg.speaker]
            verb = "keeps their mouth closed and listens" if len(others) == 1 else "keep their mouths closed and listen"
            rest = f" {' and '.join(others)} {verb}." if others else ""
            lines.append(f"From {a:.0f} s to {b:.0f} s {label(seg.speaker)} is talking: lips and jaw move clearly "
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
            f"disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene "
            f"(footsteps, the puppy, birds, wind); no music, and no voice or speech is heard.")


# ---- script checks -----------------------------------------------------------------

def check(s: Settings, script: EpisodeScript) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    sh = sheet(s)
    names = cast(sh)
    bible = script.continuity
    loc_ids = [x.id for x in bible.locations]
    prop_ids = [x.id for x in bible.props]
    for kind, ids in (("location", loc_ids), ("prop", prop_ids)):
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            errors.append(f"duplicate {kind} ids in continuity: {sorted(dup)}")

    on_screen = {c for shot in script.shots for c in shot.characters}
    unknown = on_screen - set(names)
    if unknown:
        errors.append(f"characters not on the character sheet: {sorted(unknown)}")
    support = on_screen - set(MAIN_CHARACTERS) - unknown
    if len(support) > 1:
        errors.append(f"more than one supporting character on screen: {sorted(support)}")
    dressed = {o.character for o in bible.outfits}
    for c in sorted(on_screen - dressed - unknown):
        errors.append(f"no outfit in continuity for {c}")

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
        if seg.speaker in MAIN_CHARACTERS and seg.beat != "hook":
            if not any(seg.speaker in x.characters for x in near):
                warns.append(f"{seg.start_s:g}–{seg.end_s:g}s: {seg.speaker} speaks but is not on screen")
        if seg.speaker in MAIN_CHARACTERS:
            for x in script.shots:
                overlap = min(seg.end_s, x.end_s) - max(seg.start_s, x.start_s)
                if overlap >= 1.5 and x.characters and seg.speaker not in x.characters \
                        and all(c in MAIN_CHARACTERS for c in x.characters):
                    warns.append(f"shot {x.n}: {seg.speaker} is heard for {overlap:.1f} s over a shot of "
                                 f"{', '.join(x.characters)} only; it will look like the wrong person is talking")
        for p in bible.props:
            if p.name_ta and p.name_ta in seg.narration_ta and not any(p.id in x.props for x in near):
                warns.append(f"{seg.start_s:g}–{seg.end_s:g}s: dialogue mentions {p.name_ta} ({p.id}) but no shot shows it")
        for cid, c in names.items():
            if cid in on_screen:
                continue
            name_ta = c.get("name_ta", "")
            if cid not in MAIN_CHARACTERS and name_ta and name_ta in seg.narration_ta:
                warns.append(f"{seg.start_s:g}–{seg.end_s:g}s: dialogue names {name_ta} ({cid}), who is never on screen")
    return errors, warns


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
