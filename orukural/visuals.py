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

from . import continuity, media
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
    return continuity.character_ref_prompt(s, cid)


def find_media(stem: Path, kinds: tuple[str, ...]) -> Path | None:
    for ext in kinds:
        if stem.with_suffix(ext).exists():
            return stem.with_suffix(ext)
    return None


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")


def _rel(s: Settings):
    return lambda p: str(Path(p).relative_to(s.root)) if Path(p).is_relative_to(s.root) else str(p)


def ensure_refs(s: Settings, ep_dir: Path, script: EpisodeScript, force: bool = False) -> None:
    """Make missing character, location and prop references (Gemini or dry-run placeholders).
    In Flow mode they are made from the job sheet instead."""
    if s["images"]["provider"] == "flow" and not s.dry_run:
        return
    for job in continuity.ref_jobs(s, ep_dir, script, rel=lambda p: p):
        out = Path(job["save_as"])
        if s.dry_run:
            _placeholder(out, f"REF {job['id']}", (1024, 1024) if job["aspect_ratio"] == "1:1" else (1080, 1920))
            continue
        res = _ledger(s).run(episode_id="CHARACTERS" if job["kind"] == "character_ref" else script_id(ep_dir),
                             step=job["kind"], inputs={"model": s["images"]["model"], "prompt": job["prompt"]},
                             estimate_usd=s["budget"]["estimates"]["character_ref"],
                             call=lambda: _gen_image(s, [{"type": "text", "text": job["prompt"]}], job["aspect_ratio"],
                                                     s.path("cache") / job["kind"] / out.name),
                             force=force)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(Path(res.value["file"]).read_bytes())


def script_id(ep_dir: Path) -> str:
    return ep_dir.parent.name if ep_dir.name == "dryrun" else ep_dir.name


def shot_image(s: Settings, ep_dir: Path, episode_id: str, script: EpisodeScript, shot: Shot,
               force: bool = False) -> Path:
    out = ep_dir / "images" / f"shot{shot.n:02d}.png"
    if s.dry_run:
        _placeholder(out, f"{episode_id} shot {shot.n} {shot.beat} — {shot.action_en[:80]}")
        return out
    refs = [(lab, p) for lab, p in continuity.shot_refs(s, ep_dir, script, shot) if p.exists()]
    prompt = continuity.image_prompt(s, script, shot, [lab for lab, _ in refs])
    parts: list[dict] = [{"type": "text", "text": prompt}]
    parts += [{"type": "image", "data": _b64(p), "mime_type": _mime(p)} for _, p in refs]
    res = _ledger(s).run(
        episode_id=episode_id, step="image",
        inputs={"model": s["images"]["model"], "size": s["images"]["image_size"], "prompt": prompt,
                "refs": {lab: p.stat().st_size for lab, p in refs}},
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


def shot_clip(s: Settings, ep_dir: Path, episode_id: str, script: EpisodeScript, shot: Shot, image: Path,
              force: bool = False) -> Path:
    out = ep_dir / "clips" / f"shot{shot.n:02d}.mp4"
    secs = clip_seconds(s, shot)
    out.parent.mkdir(parents=True, exist_ok=True)
    if s.dry_run:
        media.run(["-loop", "1", "-i", str(image), "-t", str(secs), "-vf",
                   f"{media.fill_frame()},fps=24",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
        return out
    prompt = continuity.clip_prompt(s, script, shot, secs)
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
    """Write flow/jobs.json + flow/README.md: everything a Flow session must make, and where to save it.
    `pool`: monthly plan credits to add on top of day 1's daily credits (0 = daily credits only)."""
    rel = lambda p: str(Path(p).relative_to(s.root))  # noqa: E731
    jobs = continuity.ref_jobs(s, ep_dir, script, rel)
    for sh in script.shots:
        if find_media(ep_dir / "images" / f"shot{sh.n:02d}", IMAGE_EXT):
            continue
        refs = continuity.shot_refs(s, ep_dir, script, sh)
        jobs.append({
            "kind": "image", "shot": sh.n, "save_as": rel(ep_dir / "images" / f"shot{sh.n:02d}.png"),
            "aspect_ratio": "9:16", "model": s["flow"]["image_model"],
            "reference_images": [rel(p) for _, p in refs],
            "prompt": continuity.image_prompt(s, script, sh, [lab for lab, _ in refs]),
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
            "prompt": continuity.clip_prompt(s, script, sh, secs),
        })
    sheet = {"episode_id": episode_id, "clip_credits": credits, "daily_credits": daily, "clip_days": day if credits else 0,
             "monthly_credits_used": pool_used,
             "jobs": jobs}
    fdir = ep_dir / "flow"
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "jobs.json").write_text(json.dumps(sheet, ensure_ascii=False, indent=1), "utf-8")
    n = episode_id.lstrip("K0")
    lines = [
        f"# Flow jobs for {episode_id}", "",
        "Make each item in Google Flow and save it to `save_as` (paths are relative to the repo)."
        + (f" Use this Flow project: {s['flow']['project_url']}" if s["flow"].get("project_url") else "")
        + " Work in this order:", "",
        "1. **References** (characters, places, props). Made once; series ones are reused by every episode.",
        "2. **Shot images**, attaching every listed reference image in the listed order.",
        f"3. **Image review.** Run `python studio.py continuity-sheet {n}` and follow the continuity-review skill "
        "(`.claude/skills/continuity-review/SKILL.md`): compare every image with the references, redo any that "
        f"drift (images are free), and mark each one `pass` in `episodes/{episode_id}/continuity_review.json`. "
        "Do not start clips until every image passes; clips cost credits.",
        f"4. **Clips**, from the reviewed images. They need {credits} credits over {sheet['clip_days']} day(s): "
        f"{daily} daily credits a day" + (f", plus {pool_used} monthly plan credits on day 1" if pool_used else "")
        + ". Spend daily credits before monthly ones. Make only today's day number; if credits run out, stop and "
        "continue after the reset. Never buy credits.",
        f"5. **Clip review.** Run `continuity-sheet {n}` again, check the first, middle and last frames of each clip, "
        "and mark clips `pass`. Redo a drifting clip only if credits allow; otherwise note it and tell the user.",
        f"6. Run `python studio.py visuals {n}`, then `render {n}`.", "",
    ]
    for j in jobs:
        head = {"character_ref": f"Character reference: {j.get('id')} → `{j['save_as']}`",
                "location_ref": f"Place reference: {j.get('id')} → `{j['save_as']}`",
                "prop_ref": f"Prop reference: {j.get('id')} → `{j['save_as']}`",
                "image": f"Shot {j.get('shot')} image → `{j['save_as']}`",
                "clip": f"Day {j.get('day')} · shot {j.get('shot')} clip ({j.get('seconds')} s, {j.get('credits')} credits) → `{j['save_as']}`"}[j["kind"]]
        lines += [f"## {head}", ""]
        if j.get("reference_images"):
            lines.append("References, in this order: " + ", ".join(f"`{r}`" for r in j["reference_images"]))
        if j.get("start_frame"):
            lines.append(f"Start frame: `{j['start_frame']}`")
        lines += [f"Aspect {j['aspect_ratio']} · {j['model']}", "", "```", j["prompt"], "```", ""]
    (fdir / "README.md").write_text("\n".join(lines), "utf-8")
    return sheet


def generate(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str, force: bool = False,
             only: set[int] | None = None) -> dict:
    ensure_refs(s, ep_dir, script, force=force)
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
            img = shot_image(s, ep_dir, episode_id, script, sh, force=force)
        clip = None
        if sh.n in animate:
            if flow_video:
                found = ep_dir / "clips" / f"shot{sh.n:02d}.mp4"
                clip = found if found.exists() else None
            else:
                clip = shot_clip(s, ep_dir, episode_id, script, sh, img, force=force)
        shots.append({"n": sh.n, "image": img.name, "clip": clip.name if clip else None})
    if missing:
        raise SystemExit(f"{episode_id}: no image yet for shots {missing}. Run `studio.py flow-sheet "
                         f"{episode_id}` and make them in Flow first.")
    manifest = {"dry_run": s.dry_run, "animated": sorted(animate),
                "animated_made": [x["n"] for x in shots if x["clip"]], "shots": shots}
    (ep_dir / "visuals.json").write_text(json.dumps(manifest, indent=1), "utf-8")
    return manifest
