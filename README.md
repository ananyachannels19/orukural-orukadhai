# orukural-studio

Production pipeline for **ஒரு குறள் • ஒரு கதை** (Orukural Orukadhai): one Thirukkural, one original story, as a 35–45 s Tamil Short/Reel, three times a week, plus an 8–10 min compilation per adhikaram.

## Status

| Phase | What | State |
|---|---|---|
| 1 | Repo, config, `data/kurals.json`, script generator | ✅ done, sample in `samples/K0301/` |
| 2 | Voice, images, clips, assembly → sample MP4 | next |
| 3 | Subtitles, branding, long-form compilation builder | |
| 4 | YouTube + Instagram publishing (private/test) | |
| 5 | Weekly scheduler, review gate, analytics | |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys yourself; .env is gitignored
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

## Script generation

`claude-sonnet-5-5` with adaptive thinking at `effort: high`, structured output validated against `orukural/schema.py`, and the system prompt (instructions + lessons + character sheet) cached. Server-side refusal fallback is on (`script.server_side_fallback`), so if the model declines a request the API retries it on Anthropic's recommended fallback model in the same call; set it to `false` to turn that off.

After generation the script is checked for things structured output can't guarantee: runtime 35–45 s, beats in order and contiguous, the verse quoted exactly, narration that fits its time slot (~11 Tamil letters/s), 6–10 shots of ≤ 8 s, both main characters on screen, no Tamil inside image prompts, title/tag/hashtag limits. Errors block the kural from moving to `scripted`; warnings show at the top of `script.md`.

## The verse data

The verses are public domain. `tools/build_kurals.py` downloads two independent datasets ([tk120404/thirukkural](https://github.com/tk120404/thirukkural) and the [thirukkural](https://pypi.org/project/thirukkural/) PyPI package), takes only verse text, numbering and chapter names, and compares every kural. 1305 match letter for letter; the 25 that differ (typos, stray characters, sandhi splits) are resolved by hand in `data/verse_overrides.yaml` with a reason for each. Four are flagged `review: true` because both sources were wrong or a classical form had to be chosen: **#143, #208, #666, #689**. The modern commentaries bundled in those datasets are never copied; the downloads stay in the gitignored `data/sources/`.
