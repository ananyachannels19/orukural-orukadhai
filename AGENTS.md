# Orukural Studio — Project Context

## Purpose

`orukural-studio` produces **ஒரு குறள் • ஒரு கதை** (*Orukural Orukadhai*):
35–45 second, 9:16 Tamil Shorts/Reels that turn one Thirukkural into an
original relationship-led story. The channel is designed for three reels per
week, with an eventual 8–10 minute compilation per adhikaram.

## Pipeline and source of truth

- `studio.py` is the CLI entry point; `orukural/` contains the pipeline.
- `config.yaml` holds non-secret provider, schedule, budget, and Flow-project
  configuration. Secrets belong only in `.env`.
- `data/kurals.json` is the canonical verse store. Preserve verse text exactly;
  the four flagged verses (#143, #208, #666, #689) require extra care.
- `data/characters.yaml`, `data/cast_log.yaml`, `data/themes.yaml`, and each
  episode's `script.json` drive casting and continuity.
- `data/lessons_learned.md` is injected into script prompts. Keep it brief,
  specific, and based on real review or analytics evidence.
- An episode lives under `episodes/KNNNN/`; its `script.json` is the
  machine-readable handoff for voice, Flow, review, and assembly.

## Creative and production invariants

- Stories use a fresh 2–3 person cast, usually adults aged 22–35. Thatha and
  Kavin are reserved for the monthly kids' special or an explicit video-call
  cameo.
- Never put a posting date, day, or time in viewer-facing scripts, cards,
  captions, titles, descriptions, or publishing assets. The schedule is
  planning-only.
- Begin with the story hook at frame one: no standalone intro. Keep a strong
  moment every 2–3 seconds and reveal a compact lesson teaser around 10–12 s.
- The Kural reveal, subtitles, logo ending, Tamil typography, and audio style
  must follow the existing signature/caption implementation consistently.
- Generate a real Flow clip for each planned visual shot: do not substitute a
  pan, zoom, punch-in, or Ken Burns movement on a still. If clips are missing,
  leave the episode waiting for Flow rather than faking motion.
- Make and approve reference images before paid clips. Preserve character,
  wardrobe, place, lighting, props, and shot continuity. One simple action and
  one explicit camera behaviour per clip; avoid text/logos in generated media.
- Do not make an adult shout at, point at, or tower over a child in a generated
  scene.
- Review image and clip continuity before assembly. Do not publish or upload
  without the user's explicit approval.

## Cost and tools

- Default mode is zero-spend: script handoff/session, Flow images and clips,
  Gemini TTS, and local FFmpeg assembly. Never silently switch to a paid
  provider or spend generation credits.
- Flow work alternates between two accounts that both hold credits: Revathi
  Satheesh (goes first, K0785) and Orukural Orukadhai
  (`orukural.orukadhai1330@gmail.com`). Identify a tab by its email, not its
  `/u/N` number. Keep every new episode in its own Flow project, created by
  Claude, and retain the project link in `config.yaml`. Sign-in is the user's.
- Skills: `/orukural-orukadhai` makes an episode (gates: script, shots, clips,
  draft); `/orukural-publish` posts; `/orukural-analytics` reads results; `continuity-review`
  checks shots. Each episode ends with `retro.md`.
- Aim for about seven clips and enforce the configured 75-credit reel cap.
  Redos beyond the planned allowance require the user's approval.
- Use `studio.py flow-sheet`, `continuity-sheet`, `flow-progress`, `voice-ab`,
  `render`, and `publish-pack` as the staged workflow; validate with the
  relevant test suite before changing pipeline behavior.

## Current working picture (1 Nov 2026)

- The implementation spans phases 1–3, including scripting, voice, Flow
  handoff/continuity review, assembly, captions, signature treatment, live
  dashboard, and publishing-package preparation. Automated publishing and
  weekly analytics remain later-phase work.
- Episodes K0301, K0788, K1330, and K0100 contain active production material.
  K0788 and K1330 have iteration artifacts; do not delete or replace them
  without a targeted request.
- Existing uncommitted changes include `config.yaml`, `data/cast_log.yaml`,
  `data/kurals.json`, character/location assets, and planning files. Treat them
  as user work and preserve them.
- The current shell does not have PyYAML installed, so `python studio.py status`
  cannot run outside the project environment until dependencies are installed.

