"""Phase 2: character references, per-shot stills and image-to-video clips.

Providers (config `images.provider` / `video.provider`):
  flow    Google Flow, driven by flow-mcp on your Mac. `studio.py flow-sheet N` writes a job
          list; the Flow session saves files to the listed paths; `studio.py visuals N`
          collects them. Free images; clips use Flow's daily free credits, spread over as
          many days as an episode needs. No pan/zoom stand-ins: assembly waits for clips.
  gemini  Gemini API (paid): images `gemini-nano-banana-2.1`, video `gemini-omni-1.1-flash`
          through the Interactions API (checked 25 Oct 2026).
Generated clip audio is always discarded at assembly; our narration and music replace it.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

import yaml

from . import media
from .config import Settings
from .ledger import Ledger
from .schema import EpisodeScript, Shot

MAIN_CHARACTERS = ("thatha", "kavin")


def _client():
    from google import genai
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY is not set. Add it to .env, or run with --dry-run.")
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _mime(path: Path) -> str:
    return "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"


def _ledger(s: Settings) -> Ledger:
    return Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])


def _sheet(s: Settings) -> dict:
    return yaml.safe_load(s.file("characters_file").read_text("utf-8"))


# ---- images ------------------------------------------------------------------------

def _gen_image(s: Settings, parts: list[dict], aspect: str, out: Path) -> tuple[dict, float, dict]:
    cfg = s["images"]
    interaction = _client().interactions.create(
        model=cfg["model"],
        input=parts,
        response_format={"type": "image", "aspect_ratio": aspect, "image_size": cfg["image_size"]},
    )
    img = interaction.output_image
    if not img or not img.data:
        raise RuntimeError(f"no image returned (safety filter or empty response) for {out.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(img.data))
    return {"file": str(out)}, cfg["price_per_image"][cfg["image_size"]], {
        "provider": "gemini", "model": cfg["model"], "interaction_id": getattr(interaction, "id", None)}


def _placeholder(out: Path, label: str, size: tuple[int, int] = (1080, 1920)) -> None:
    """Dry-run stand-in: a labelled card, so assembly can be tested without spending."""
    from PIL import Image, ImageDraw, ImageFont
    hue = sum(map(ord, label)) % 360
    img = Image.new("RGB", size, tuple(int(80 + 60 * abs(((hue / 60 + k) % 6) - 3) / 3) for k in (0, 2, 4)))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
    except OSError:
        font = ImageFont.load_default()
    y = size[1] // 3
    for line in re.findall(r".{1,22}(?:\s|$)", label):
        d.text((60, y), line.strip(), fill="white", font=font)
        y += 80
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def character_prompt(s: Settings, cid: str) -> str:
    sheet = _sheet(s)
    c = sheet["characters"][cid]
    return (
        f"Character reference sheet for an animated series. {c['name']}, {c['age']} years old. {c['look'].strip()} "
        f"Show the same character twice side by side: full body standing front view, and a head-and-shoulders "
        f"close-up. Neutral expression with a hint of their personality: {c['voice_and_manner'].strip()} "
        f"Plain light warm-grey background. Style: {sheet['world']['visual_style'].strip()}"
    )


def find_media(stem: Path, kinds: tuple[str, ...]) -> Path | None:
    for ext in kinds:
        if stem.with_suffix(ext).exists():
            return stem.with_suffix(ext)
    return None


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")


def character_refs(s: Settings, force: bool = False) -> dict[str, Path]:
    """One reference image per main character, made once and committed."""
    cdir = s.root / s["images"]["characters_dir"]
    if s.dry_run:  # placeholders must never land in the committed assets folder
        cdir = s.path("cache") / "dry_run_characters"
    refs = {}
    for cid in MAIN_CHARACTERS:
        found = find_media(cdir / cid, IMAGE_EXT)
        out = found or cdir / f"{cid}.png"
        refs[cid] = out
        if found and not force:
            continue
        prompt = character_prompt(s, cid)
        if s.dry_run:
            _placeholder(out, f"REF {cid}", (1024, 1024))
            continue
        if s["images"]["provider"] == "flow":
            continue  # made in Flow from the job sheet
        res = _ledger(s).run(episode_id="CHARACTERS", step="character_ref",
                             inputs={"model": s["images"]["model"], "prompt": prompt},
                             estimate_usd=s["budget"]["estimates"]["character_ref"],
                             call=lambda: _gen_image(s, [{"type": "text", "text": prompt}], "1:1",
                                                     s.path("cache") / "character_ref" / f"{cid}.png"),
                             force=force)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(Path(res.value["file"]).read_bytes())
    return refs


def shot_image(s: Settings, ep_dir: Path, episode_id: str, shot: Shot, refs: dict[str, Path], force: bool = False) -> Path:
    out = ep_dir / "images" / f"shot{shot.n:02d}.png"
    if s.dry_run:
        _placeholder(out, f"{episode_id} shot {shot.n} {shot.beat} — {shot.action_en[:80]}")
        return out
    used = [c for c in shot.characters if c in refs][:4]  # model takes up to 4 character references
    parts: list[dict] = [{"type": "text", "text": shot.image_prompt_en}]
    if used:
        names = ", ".join(f"reference image {i + 1} is {c}" for i, c in enumerate(used))
        parts[0]["text"] += (f" Keep each character's face, hair, body and clothes exactly as in the attached "
                             f"reference images ({names}). Do not copy the reference layout or background.")
        parts += [{"type": "image", "data": _b64(refs[c]), "mime_type": _mime(refs[c])} for c in used]
    ref_hashes = {c: refs[c].stat().st_size for c in used}
    res = _ledger(s).run(
        episode_id=episode_id, step="image",
        inputs={"model": s["images"]["model"], "size": s["images"]["image_size"], "prompt": parts[0]["text"], "refs": ref_hashes},
        estimate_usd=s["images"]["price_per_image"][s["images"]["image_size"]],
        call=lambda: _gen_image(s, parts, "9:16", s.path("cache") / "image" / f"{episode_id}_shot{shot.n:02d}.png"),
        force=force,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(Path(res.value["file"]).read_bytes())
    return out


# ---- clips -------------------------------------------------------------------------

def animated_shots(s: Settings, script: EpisodeScript) -> set[int]:
    mode = s["video"]["animate"]
    shots = script.shots
    if mode == "all":
        return {sh.n for sh in shots}
    if mode == "none" or not shots:
        return set()
    limit = s["video"]["max_animated_shots"]
    chosen = [shots[0].n, shots[-1].n]
    for sh in sorted(shots[1:-1], key=lambda x: (x.motion_priority, x.n)):
        if len(chosen) >= limit:
            break
        chosen.append(sh.n)
    return set(chosen[:limit])


def clip_seconds(s: Settings, shot: Shot) -> int:
    lo, hi = s["video"]["clip_seconds"]
    return int(min(hi, max(lo, -(-(shot.end_s - shot.start_s) // 1))))


def _gen_clip(s: Settings, image: Path, prompt: str, out: Path) -> tuple[dict, float, dict]:
    cfg = s["video"]
    client = _client()
    interaction = client.interactions.create(
        model=cfg["model"],
        input=[
            {"type": "image", "data": _b64(image), "mime_type": _mime(image)},
            {"type": "text", "text": prompt},
        ],
        generation_config={"video_config": {"task": "image_to_video"}},
        response_format={"type": "video", "aspect_ratio": "9:16", "resolution": cfg["resolution"], "delivery": "uri"},
    )
    video = interaction.output_video
    if not video:
        raise RuntimeError(f"no video returned (safety filter or empty response) for {out.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    if getattr(video, "data", None):
        out.write_bytes(base64.b64decode(video.data))
    else:
        name = re.search(r"files/[^/:?]+", video.uri).group(0)
        deadline = time.time() + 900
        while True:
            info = client.files.get(name=name)
            state = getattr(info.state, "name", str(info.state))
            if state == "ACTIVE":
                break
            if state == "FAILED" or time.time() > deadline:
                raise RuntimeError(f"video file {name} is {state}")
            time.sleep(5)
        data = client.files.download(file=info)
        out.write_bytes(data)
    seconds = media.duration(out)
    return {"file": str(out), "seconds": seconds}, seconds * cfg["price_per_second"], {
        "provider": "gemini", "model": cfg["model"], "clip_seconds": round(seconds, 2),
        "interaction_id": getattr(interaction, "id", None)}


def shot_clip(s: Settings, ep_dir: Path, episode_id: str, shot: Shot, image: Path, force: bool = False) -> Path:
    out = ep_dir / "clips" / f"shot{shot.n:02d}.mp4"
    secs = clip_seconds(s, shot)
    out.parent.mkdir(parents=True, exist_ok=True)
    if s.dry_run:
        media.run(["-loop", "1", "-i", str(image), "-t", str(secs), "-vf",
                   f"{media.fill_frame()},fps=24",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
        return out
    prompt = (f"{shot.motion_prompt_en.strip()} Camera: {shot.camera_en.strip()} "
              f"Keep the characters exactly as they look in the image. About {secs} seconds, one continuous shot, "
              f"no cuts, no on-screen text, no dialogue or speech.")
    res = _ledger(s).run(
        episode_id=episode_id, step="clip",
        inputs={"model": s["video"]["model"], "res": s["video"]["resolution"], "prompt": prompt,
                "image": image.stat().st_size},
        estimate_usd=secs * s["video"]["price_per_second"],
        call=lambda: _gen_clip(s, image, prompt, s.path("cache") / "clip" / f"{episode_id}_shot{shot.n:02d}.mp4"),
        force=force,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(Path(res.value["file"]).read_bytes())
    return out


def flow_sheet(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str, pool: int = 0) -> dict:
    """`pool`: monthly plan credits to add on top of day 1's daily credits (0 = daily credits only)."""
    """Write flow/jobs.json + flow/README.md: everything a Flow session must make, and where to save it."""
    rel = lambda p: str(Path(p).relative_to(s.root))  # noqa: E731
    cdir = s.root / s["images"]["characters_dir"]
    refs = {cid: find_media(cdir / cid, IMAGE_EXT) for cid in MAIN_CHARACTERS}
    jobs = []
    for cid, found in refs.items():
        if not found:
            jobs.append({"kind": "character_ref", "save_as": rel(cdir / f"{cid}.png"), "aspect_ratio": "1:1",
                         "model": s["flow"]["image_model"], "prompt": character_prompt(s, cid)})
    for sh in script.shots:
        if find_media(ep_dir / "images" / f"shot{sh.n:02d}", IMAGE_EXT):
            continue
        used = [c for c in sh.characters if c in refs][:4]
        jobs.append({
            "kind": "image", "shot": sh.n, "save_as": rel(ep_dir / "images" / f"shot{sh.n:02d}.png"),
            "aspect_ratio": "9:16", "model": s["flow"]["image_model"],
            "reference_images": [rel(cdir / f"{c}.png") for c in used],
            "prompt": sh.image_prompt_en + (
                f" Keep each character's face, hair, body and clothes exactly as in the reference images "
                f"({', '.join(used)})." if used else ""),
        })
    credits, day, day_used, pool_used = 0, 1, 0, 0
    daily = s["flow"]["daily_credits"]
    table = {int(k): v for k, v in s["flow"]["credits_per_clip"].items()}
    for n in sorted(animated_shots(s, script)):
        sh = next(x for x in script.shots if x.n == n)
        if (ep_dir / "clips" / f"shot{n:02d}.mp4").exists():
            continue
        secs = min(table, key=lambda k: (k < clip_seconds(s, sh), abs(k - clip_seconds(s, sh))))
        credits += table[secs]
        cap = daily + (pool if day == 1 else 0)  # monthly credits only top up day 1
        if day_used + table[secs] > cap:  # spread clips over days as Flow's daily credits reset
            day, day_used = day + 1, 0
        day_used += table[secs]
        if day == 1:
            pool_used = max(0, day_used - daily)
        jobs.append({
            "kind": "clip", "shot": n, "day": day, "priority": sh.motion_priority,
            "save_as": rel(ep_dir / "clips" / f"shot{n:02d}.mp4"),
            "start_frame": rel(ep_dir / "images" / f"shot{n:02d}.png"),
            "model": s["flow"]["video_model"], "seconds": secs, "aspect_ratio": "9:16", "credits": table[secs],
            "prompt": (f"{sh.motion_prompt_en.strip()} Camera: {sh.camera_en.strip()} Keep the characters exactly as "
                       f"they look in the start frame. One continuous shot, no cuts, no text, no dialogue."),
        })
    sheet = {"episode_id": episode_id, "clip_credits": credits, "daily_credits": daily, "clip_days": day if credits else 0,
             "monthly_credits_used": pool_used,
             "jobs": jobs}
    fdir = ep_dir / "flow"
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "jobs.json").write_text(json.dumps(sheet, ensure_ascii=False, indent=1), "utf-8")
    lines = [
        f"# Flow jobs for {episode_id}", "",
        "Make each item in Google Flow and save it to `save_as` (paths are relative to the repo).",
        "Do images first: clips start from the saved shot image. Attach the listed reference images.",
        f"Clips need {credits} credits over {sheet['clip_days']} day(s): {daily} daily credits a day"
        + (f", plus {pool_used} monthly plan credits on day 1" if pool_used else "") + ". Spend daily credits before "
        "monthly ones. Make only the clips for today's day number; if credits run out early, stop and continue after "
        "the reset. Never buy credits.",
        "Then run `python studio.py visuals " + episode_id.lstrip("K0") + "` to collect everything.", "",
    ]
    for j in jobs:
        head = {"character_ref": f"Character reference → `{j['save_as']}`",
                "image": f"Shot {j.get('shot')} image → `{j['save_as']}`",
                "clip": f"Day {j.get('day')} · shot {j.get('shot')} clip ({j.get('seconds')} s, {j.get('credits')} credits) → `{j['save_as']}`"}[j["kind"]]
        lines += [f"## {head}", ""]
        if j.get("reference_images"):
            lines.append("References: " + ", ".join(f"`{r}`" for r in j["reference_images"]))
        if j.get("start_frame"):
            lines.append(f"Start frame: `{j['start_frame']}`")
        lines += [f"Aspect {j['aspect_ratio']} · {j['model']}", "", "```", j["prompt"], "```", ""]
    (fdir / "README.md").write_text("\n".join(lines), "utf-8")
    return sheet


def generate(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str, force: bool = False,
             only: set[int] | None = None) -> dict:
    refs = character_refs(s)
    animate = animated_shots(s, script)
    flow_images = s["images"]["provider"] == "flow" and not s.dry_run
    flow_video = s["video"]["provider"] == "flow" and not s.dry_run
    shots, missing = [], []
    for sh in script.shots:
        if only and sh.n not in only:
            continue
        if flow_images:
            img = find_media(ep_dir / "images" / f"shot{sh.n:02d}", IMAGE_EXT)
            if not img:
                missing.append(sh.n)
                continue
        else:
            img = shot_image(s, ep_dir, episode_id, sh, refs, force=force)
        clip = None
        if sh.n in animate:
            if flow_video:
                found = ep_dir / "clips" / f"shot{sh.n:02d}.mp4"
                clip = found if found.exists() else None
            else:
                clip = shot_clip(s, ep_dir, episode_id, sh, img, force=force)
        shots.append({"n": sh.n, "image": img.name, "clip": clip.name if clip else None})
    if missing:
        raise SystemExit(f"{episode_id}: no image yet for shots {missing}. Run `studio.py flow-sheet "
                         f"{episode_id}` and make them in Flow first.")
    manifest = {"dry_run": s.dry_run, "animated": sorted(animate),
                "animated_made": [x["n"] for x in shots if x["clip"]], "shots": shots}
    (ep_dir / "visuals.json").write_text(json.dumps(manifest, indent=1), "utf-8")
    return manifest
