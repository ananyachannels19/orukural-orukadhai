# orukural-studio

Production pipeline for **ஒரு குறள் • ஒரு கதை** (Orukural Orukadhai): one Thirukkural, one original story, as a 35–45 s Tamil Short/Reel, three times a week, plus an 8–10 min compilation per adhikaram.

## Status

| Phase | What | State |
|---|---|---|
| 1 | Repo, config, `data/kurals.json`, script generator | ✅ done, sample in `samples/K0301/` |
| 2 | Voice, images, clips, assembly → sample MP4 | ✅ built, tested in dry-run; real sample next, on your Mac |
| 3 | Subtitles, branding, long-form compilation builder | |
| 4 | YouTube + Instagram publishing (private/test) | |
| 5 | Weekly scheduler, review gate, analytics | |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add GEMINI_API_KEY yourself (free at aistudio.google.com/apikey); .env is gitignored
python studio.py status
```

FFmpeg is needed from phase 2 (`brew install ffmpeg`).

## Commands (phase 1)

```bash
python studio.py plan -n 3              # the next kurals, one adhikaram at a time
python studio.py script 301             # write script + shot list + metadata → episodes/K0301/
python studio.py script 301 --dry-run   # same, no API call, placeholder content
python studio.py script-check 301       # after hand-editing episodes/K0301/script.json
python studio.py spend                  # what each episode has cost
python studio.py data build             # rebuild data/kurals.json from the sources
```

Each episode folder holds `script.json` (the machine-readable script every later phase reads), `script.md` (for you to read), `youtube_description.txt`, and `script_prompt.md` (exactly what was sent to Claude).

## How the pieces fit

- **`config.yaml`**: schedule, adhikaram order (anger, patience, friendship, hard work, speech, wealth first), episode timing, model, budget caps, link placeholders. No secrets.
- **`data/kurals.json`**: all 1330 kurals with number, verse, adhikaram, paal, iyal, theme and status (`planned → scripted → rendered → approved → scheduled → posted`). Meanings are empty until an episode is scripted, then hold our own wording.
- **`data/characters.yaml`**: the fixed character sheet (Thatha, Kavin, a small supporting cast, the town). Every script and image prompt is built from it.
- **`data/lessons_learned.md`**: read into every script prompt; the weekly analytics step (phase 5) rewrites its "From analytics" section.
- **`data/pronunciation_fixes.yaml`**: respellings for the voice model (phase 2).
- **`orukural/ledger.py`**: every paid call goes through it. It returns a cached result if the same inputs already succeeded, refuses a call that would push an episode over `budget.per_episode_cap`, and logs real spend to `logs/spend.jsonl`.

## Zero-spend mode (default)

Until the channel earns, nothing in the weekly run costs money:

| Step | Free route | Paid route (switch in `config.yaml`) |
|---|---|---|
| Script | Claude writes it in the weekly Claude session (`script.provider: session`) | Anthropic API, ~$0.10 |
| Images | Google Flow via flow-mcp on your Mac (`images.provider: flow`) | Gemini `gemini-nano-banana-2.1`, ~$0.05 each |
| Clips | Google Flow on Google AI Plus: 50 credits a day + 200 a month; one episode (10 clips) ≈ 85 credits (`video.provider: flow`) | Gemini `gemini-omni-1.1-flash`, ~$0.10/s |
| Voice | Gemini TTS `gemini-3.8-flash-tts` on a free AI Studio key, no billing or card (`voice.provider: gemini_tts`) | Google Cloud TTS Chirp 3 HD (needs Cloud billing), or ElevenLabs `eleven_v4` (paid plan for commercial use) |
| Assembly | FFmpeg, local | – |

Flow has no API we can call from Python, so the hand-off is file based: `studio.py flow-sheet 301` writes `episodes/K0301/flow/README.md` with every image and clip to make, the prompt, the reference images to attach, and the exact path to save it to. A Claude Code session on your Mac with flow-mcp works through that list. `studio.py visuals 301` then collects the files. Every shot is a real Flow clip, and the sheet groups the clips into days that fit the 50 daily credits ("Day 1", "Day 2"). There is no pan or zoom anywhere: if a clip is still missing, `assemble` stops and lists the shots still waiting (`assembly.missing_clip: wait`), and you finish them after the credits reset. With 3 episodes a week at about 2 days of credits each, Flow clips are made almost every day, not only on Sunday.

**Credit plan (Google AI Plus).** Daily credits don't carry over, so they are always spent first. 50 a day is about 1,500 a month, and 3 episodes a week need about 1,100, so daily credits alone keep the schedule. The 200 monthly credits are the reserve: `studio.py flow-sheet 301 --use-monthly` adds 35 of them to day 1 so a whole episode is made in one day (about 5 such days a month). Use that to catch up or build a lead before launch, and keep roughly 100 for redoing clips that come out wrong.

## Commands (phase 2)

```bash
python studio.py voice-test            # one kural line in 8 Tamil voices → review/voice_test/, pick by ear
python studio.py flow-sheet 301        # what to make in Flow and where to save it (refs, images, review, clips)
python studio.py continuity-sheet 301  # contact sheets + review file for the continuity check
python studio.py render 301            # voice → collect visuals → assemble → episodes/K0301/render/K0301_draft.mp4
python studio.py render 301 --dry-run  # whole pipeline with placeholder cards and silence, in episodes/K0301/dryrun/
```

- **Voice** (`orukural/voice.py`): each script segment is voiced on its own. Narrator, Thatha and Kavin can have separate voices (`speaker_voices`). `data/pronunciation_fixes.yaml` respellings are applied to the spoken text only.
- **Visuals** (`orukural/visuals.py`): reference images for characters, places and props are attached to every shot image (see Consistency above). `video.animate: all` (default) makes a clip for every shot; `key` would animate only the first, last and highest `motion_priority` shots, and `none` none.
- **Assembly** (`orukural/assemble.py`): each segment gets its planned time or the real voice length, whichever is longer; shots move with their segments. Shots are shown as made, with no pan, zoom or punch-in (`assembly.punch_in: 1.0`). Narration is mixed over a track from `assets/music/` (ducked under speech) and loudness-normalised to −14 LUFS. Subtitles, kural badge, on-screen Tamil text and the end card come in phase 3.

## Studio Live (watch every step)

```bash
python studio.py live                  # opens http://localhost:8765 and updates every 2 s
python studio.py live --host 0.0.0.0   # also reachable from a phone on the same Wi-Fi
```

One page shows the episode's ten stages, what is running right now (with a stall timer), each shot's image and clip as they land (hover to play, click for the prompt and every try), Flow credits, the free TTS quota with its reset time, paid spend, failures and retries with what was done about them, and the posting calendar. It only reads files; nothing on it changes the pipeline.

Most of it comes from what is already on disk (episode folders, `continuity_review.json`, `flow/jobs.json`, `logs/spend.jsonl`). Failures, retries and Flow credits come from `logs/events.jsonl`, written by `orukural.live.emit()` in the pipeline, and by the Flow session on the Mac with:

```bash
python studio.py event 301 clips start --shot 2 --attempt 3 --detail "Making shot 2 clip"
python studio.py event 301 clips done  --shot 2 --credits 12 --credits-left 219 --detail "Shot 2 clip made"
python studio.py event 301 clips blocked --shot 2 --detail "Flow showed an unusual activity check"
```

Statuses: `start`, `done`, `fail`, `retry`, `wait`, `blocked` (shows as "Needs you" until work on that step goes on), `info`.

## Consistency (characters, places, props, dialogue)

An episode has 10 separately generated shots, so anything left to chance drifts: a shawl appears, the puppy's ear switches sides, the light goes back from sunset to afternoon. Consistency is built in at three layers (`orukural/continuity.py`):

1. **The bible.** `data/characters.yaml` fixes the cast (face and body in `look`, clothes in `wardrobe`), eight recurring places, and how people address each other (`speech`). Each script adds a `continuity` block: this episode's places with their light and blocking (who stands where, facing which way), every prop described exactly, and one outfit per character. Image and clip prompts are **built from the bible**, not retyped per shot, so a detail can't drift between shots. The shot's own `image_prompt_en` only says the composition and action.
2. **Reference images.** Every character (supporting ones too), every recurring place (`assets/locations/`, made once and reused by every episode) and every episode prop (`episodes/<id>/refs/props/`) gets one reference image, attached to every shot that shows it, in a fixed order.
3. **Checks.**
   - On the script (`script-check`): unknown places, props or characters; a character on screen with no outfit; more than one supporting character; a character who speaks but is never on screen during the line; a prop the dialogue names (`name_ta`) but no nearby shot shows.
   - On the pictures: `studio.py continuity-sheet 301` makes contact sheets (references, all shot images, and first/middle/last frames of every clip) and `episodes/<id>/continuity_review.json`. The Mac session follows `.claude/skills/continuity-review/SKILL.md` to compare them, redoes failing images (free) before any clip is made, and marks each shot `pass`. `assemble` refuses to render until every image and clip passes (`continuity.require_review`).

## Script generation

`claude-sonnet-5-5` with adaptive thinking at `effort: high`, structured output validated against `orukural/schema.py`, and the system prompt (instructions + lessons + character sheet) cached. Server-side refusal fallback is on (`script.server_side_fallback`), so if the model declines a request the API retries it on Anthropic's recommended fallback model in the same call; set it to `false` to turn that off.

After generation the script is checked for things structured output can't guarantee: runtime 35–45 s, beats in order and contiguous, the verse quoted exactly, narration that fits its time slot (~11 Tamil letters/s), 6–10 shots of ≤ 8 s, both main characters on screen, no Tamil inside image prompts, title/tag/hashtag limits. Errors block the kural from moving to `scripted`; warnings show at the top of `script.md`.

## The verse data

The verses are public domain. `tools/build_kurals.py` downloads two independent datasets ([tk120404/thirukkural](https://github.com/tk120404/thirukkural) and the [thirukkural](https://pypi.org/project/thirukkural/) PyPI package), takes only verse text, numbering and chapter names, and compares every kural. 1305 match letter for letter; the 25 that differ (typos, stray characters, sandhi splits) are resolved by hand in `data/verse_overrides.yaml` with a reason for each. Four are flagged `review: true` because both sources were wrong or a classical form had to be chosen: **#143, #208, #666, #689**. The modern commentaries bundled in those datasets are never copied; the downloads stay in the gitignored `data/sources/`.
