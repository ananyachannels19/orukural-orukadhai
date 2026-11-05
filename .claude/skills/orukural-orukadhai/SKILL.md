---
name: orukural-orukadhai
description: Make the next Orukural Orukadhai (ஒரு குறள் • ஒரு கதை) Thirukkural story reel end to end in Google Flow, with approval gates for the script, shots, clips and draft. Use for "make the next kural in the pipeline", "make K0785", or any new episode. Does not post; posting is the orukural-publish skill.
---

# Orukural Orukadhai: make one episode

Takes the next kural in the lineup from nothing to an approved draft. It stops at four gates and waits for Ananya's explicit approval at each. It never uploads or posts anything (use `orukural-publish`).

Repo: `/Users/ananya-24962/AI/Claude/orukural-studio`. Work only under `/Users/ananya-24962/AI`, never `~/Documents`. Read `AGENTS.md` first. Background and history: `KURAL_CREATION_MEMORY.md` (move to `docs/` later). Never read or print `.env`.

## Rules that never bend

1. **Approval is per gate and per episode.** "approved", "go ahead" or an option pick passes the gate. A message ending in "?" is a question, not approval. Approval for one episode never carries to the next.
2. **Zero spend by default.** Flow images, Flow clips, Gemini TTS free tier, local FFmpeg. Never switch to a paid provider.
3. **Free fixes need no asking** (re-timing, re-cutting, moving cards, regenerating images, remaking voice if quota allows). **Any paid retry (Flow clip) needs her OK first**, with the credit cost stated. Flow refusals and failed uploads cost nothing.
4. **Credits:** cap 75 per reel (about 7 clips; 4 s = 7 credits, 8 s = 12). Stop at the cap and ask. If the account runs low, stop and resume next day rather than overspend.
5. **Clips:** a real Flow clip for every visual shot. Never fake motion on a still. Subtle zoom 1.0 to 1.08 on a real clip is allowed. Download every clip as **"1080p Upscaled"** the first time (free), never 720p first.
6. **No "next kural" teaser. No posting day, date or time on anything viewers see.** An occasional "அப்படிப்பட்ட <உறவு>-ஐ டேக் பண்ணுங்க!" ending is fine, not every time. No "save" text.
7. **Child safety:** no adult shouting at, pointing at, grabbing or towering over a child. Angry lines get "frowning, no smile".
8. **Report progress every 2–3 minutes** during long work and run renders in the background. Review your own work frame by frame before showing her; she should never have to find a flaw first.
9. **Never type or ask for passwords.** Sign-in is hers. Keys live only in `.env`; never print or paste one.
10. Don't delete or overwrite earlier episodes' files, edit `flow-mcp`, or touch uncommitted user work without a targeted request.

Stage-by-stage detail, prompt wording and QC lists: `reference.md` in this folder. Read the section you need when you reach that stage.

## Stage 0: Preflight (free)

1. Run `python studio.py plan` / `status` (needs the project venv; if PyYAML is missing, use the `.venv`). Pick the next `lineup` kural in `config.yaml` with no `episodes/KNNNN/` folder. After the lineup, rotate by theme from `data/themes.yaml` (vary relationship type and adhikaram, avoid repeating the last three). Read the kural, meanings and adhikaram from `data/kurals.json` (extra care for #143, #208, #666, #689).
2. Read `data/lessons_learned.md`, the last three `episodes/*/retro.md`, `data/cast_log.yaml`, and `reports/weekly/suggestions.md` (the latest weekly analytics suggestions). Tell her in one line what you are carrying over. Suggestions that need only a script or prompt choice (hook type, bond, length, ending) may be applied and named; any change to format, style, animation or code must be put to her first and discussed before use.
3. **Flow account:** alternate between the two accounts. Revathi Satheesh was used for K0467 v2 and goes first for K0785; the next episode uses Orukural Orukadhai (`orukural.orukadhai1330@gmail.com`), then alternate. Tiebreak: more credits. Confirm which account a tab is on by its email, not by the `/u/N` number (it changes with sign-in order). Say which account you will use before creating anything.
4. **Flow connection:** check the `flow` tools respond and the Chrome profile (`~/.flow-mcp/chrome-profile`, port 9333) is signed in. If signed out or the connection drops, stop and ask her to sign in or reconnect, then resume. Don't retry endlessly.
5. Check credits, and the Gemini TTS quota (10 requests a day; reset about 12:30 IST). Plan the voice so a whole episode needs the fewest requests. If the quota will not cover it, do every other stage and hold the voice step; say when it resets. Extra keys from `.env` (`GEMINI_API_KEY_2`...) only if she has said so for this episode.
6. Create `episodes/KNNNN/` with `episode.yaml` (status, flow account and project, gate approvals with dates, credits planned/used).

## Stage 1: Script (free) → GATE 1

Write `script.json` and `script.md` per `prompts/script_system.md` and `prompts/episode_script.schema.json`. Checks before you show it (details in `reference.md`):

- **Unique:** the situation, hook, location, props and cast differ from every earlier episode (compare `cast_log.yaml`, retros, `script.md` loglines). New 2–3 person adult cast, differing from recent ones in at least two traits; names, looks and voices not reused within 12 episodes.
- **Hooks:** write three (question, tense moment, surprising line); choose one with tension at frame one and a card by 3 s; lesson teaser on screen at 10–12 s; something happens every 2–3 s; kural at about 25–35 s, narrator only (Charon); lesson card; loop-friendly last shot. Don't use the same hook type five times running.
- **Timing:** about 11 Tamil letters per second; total 35–45 s; deliberate silent beats are a gap between one segment's `end_s` and the next `start_s`, and the shot must span the same gap.
- **Clarity:** spoken Tamil, English loanwords written in Tamil script, no stray non-Tamil characters (they slow Gemini TTS about 2×), no bare "கால்", one action per shot.
- Run `python studio.py script-check N`.

Show her the script (open `script.md`) and **wait for approval.** After approval, commit the script locally (`KNNNN script approved`); text only, media is gitignored.

## Stage 2: Flow project, references and shot images (free) → GATE 2

1. Create a **new Flow project** on the chosen account, titled `KNNNN – <short title>`. Save the link: `python studio.py flow-project N <link>` and set it in `episode.yaml`.
2. Make references: a sheet per character, a plate per place, **one master per recurring object** (make the place from the object's tile). Then one still per shot, referencing existing tiles by name, never re-uploading PNGs. At most 3 references per image (characters, place, props).
3. `python studio.py flow-sheet N`, then `continuity-sheet N`; run the `continuity-review` skill on the images. Fix failures yourself (free) before she sees them.
4. Open the contact sheet for her. **GATE 2: wait for shot approval.** Redo what she flags (free).

## Stage 3: Voice (free, quota-limited)

Voice comes **before clips** so lip sync fits the final audio. Words only (no delivery notes in the text); shape with punctuation. `python studio.py voice N`. Check each line: speaker voice correct, pitch (adult male about 85–165 Hz, child above 170), whisper transcript matches, pace matches the script. Don't re-run `voice --force` casually; it spends requests and may overwrite hand edits.

## Stage 4: Clips (credits) → GATE 3

One clip at a time from the approved stills, about 7 clips. Each prompt carries the **exact spoken line in quotes**, one simple action, one camera behaviour, "exactly one <object>", "frowning, no smile" on angry lines, and no text or logos. Download as 1080p Upscaled into `episodes/KNNNN/clips/`; confirm each file is the shot you asked for. After each clip, check mouth span against the line length (speed change must stay within 0.9–1.1×), phone at the ear, no duplicate props, no floating objects, door and place intact. Record credits in `episode.yaml` and `logs/spend.jsonl` (`studio.py spend`).

Show her the clips. **GATE 3: wait for clip approval.** Any paid redo needs her OK with the cost.

## Stage 5: Draft (free) → GATE 4

`python studio.py assemble N` (in the background, with progress notes). Run the QC checklist in `reference.md` frame by frame, fix what you find for free, and list what you accept as small. Open the draft for her in QuickTime. **GATE 4: wait for approval or a timestamped fix list.** Apply fixes and repeat.

## Stage 6: Final and publish pack (free), only after Gate 4

`python studio.py assemble N --final`, then `python studio.py publish-pack N`. Stop there. Posting is a separate decision: hand over to `orukural-publish`.

## Stage 7: Retro

Write `episodes/KNNNN/retro.md` from `retro_template.md` after Gate 4 and update it after the final. Commit the retro locally. Pushing to GitHub happens in `orukural-publish` after posting. Propose (never silently apply) edits to `data/lessons_learned.md` for lessons that repeated across two or more episodes or that she confirmed. Keep that file short.
