---
name: orukural-publish
description: Post an approved Orukural Orukadhai reel to YouTube Shorts and Instagram Reels at the highest video quality. Use only when Ananya asks to post or hold a posting reminder for an episode (for example K0100). Irreversible; needs her explicit go-ahead. Analytics is the orukural-analytics skill.
---

# Orukural Orukadhai: publish

Posting is public and cannot be undone. This skill never runs as part of making an episode.

## Video quality: always the full-quality final

Upload the original final render to both platforms. K0467's Instagram reel went up as a 9 MB two-pass copy (about 2 Mbps) because of a tool upload limit, while the final is 37 MB at about 7.3 Mbps. Do not repeat that.
- Before posting, run `ffprobe` on the file and confirm 1080x1920, H.264, about 7 Mbps or more, AAC 320k, 30 fps. Tell her the result.
- Ananya picks the file in the browser dialog herself, so the 10 MB limit of Claude's own upload tool does not apply. Never substitute a reduced copy. If any step would force a smaller file, stop and tell her instead of downscaling.
- Instagram will recompress; give it the best source. Use the 1080p cover and thumbnail, not a compressed one.

## Before anything

1. Confirm the episode's final exists: `episodes/KNNNN/render/` or `review/KNNNN/` final, the publish pack (`publish/KNNNN_post.md`, `KNNNN_cover.jpg`; make with `python studio.py publish-pack N` if missing). Check `episode.yaml` shows Gate 4 approved.
2. Read the pack and check it: no schedule line, no date or day, no bell emoji, no "next kural" teaser, no "save" text, no duplicate lines, the kural text matches `data/kurals.json`, hashtags 3–5 (`#திருக்குறள் #thirukkural #ஒருகுறள்ஒருகதை` + one theme tag; add `#tamilstories` on Instagram), the AI disclosure line present:
   "This video uses AI-generated visuals and an AI narrator voice. Story, script and meaning are original to this channel."
3. **Get an explicit go-ahead for this episode**: "post now", "approved", or a named time. A message ending in "?" is a question, not a go-ahead. If she names a time or day (she may hold a reel, such as a festival reel for Saturday), do nothing until then and offer a reminder. Never put the time in viewer-facing text.
4. Check neither platform already has the episode.

## Posting (Claude desktop app built-in browser)

Browser pane: Cmd+Shift+B. The browser cannot attach local files, so Ananya makes four picks; open Finder with the file selected before each one.

1. Sign-in: if YouTube or Instagram (orukural.orukadhai) is signed out, ask her to sign in and reply "signed in". Never type or ask for passwords.
2. **YouTube Studio:** she picks the video ("picked"). Fill title (`குறள் N | <hook> | Thirukkural Story #Shorts`, max 100 chars), description, tags. Not made for kids. Altered or synthetic content = Yes. She picks the thumbnail ("thumb"). Public. Stay on the page until upload reaches 100%, then Publish.
3. **Instagram:** she picks the video ("ig picked"), keep Original 9:16 and sound on; she picks the cover ("cover"). Paste the caption unchanged. Turn **Add AI label ON before Share** (it cannot be added on the web afterwards). Share to Facebook off. Share once; it can take about 2 minutes.
4. Send her both live links and record them in `episode.yaml` and the retro.

## Comments

No pinned comment for now (channel verification not done, and she wants to wait on comments until the channel has more reels). Don't post or pin one unless she asks.

## After posting: update the repo

Repo: `https://github.com/ananyachannels19/orukural-orukadhai` (should be private; check before pushing). Once both links are live:
1. Add the episode to `data/published.yaml` (kural, YouTube and Instagram links) and update `episodes/KNNNN/episode.yaml` (links, status posted, AI label on, file quality used). Add the final's `ffprobe` result to the retro.
2. Make sure `data/cast_log.yaml`, `data/lessons_learned.md` (only approved edits), `config.yaml` and the episode's `script.json`, `script.md`, `edit.json`, `retro.md` and `publish/*.md` are current.
3. Commit only text and data (media is gitignored: clips, renders, voices, images). Message: `KNNNN published: <title>`. Never commit `.env`, keys or tokens; run `git status` and read the file list first.
4. `git pull --rebase origin main`, then `git push origin HEAD:main`. Never force-push. If push fails (no credentials, repo not private, conflict), stop and tell Ananya; do not ask for or type a token or password.

Then hand off to `orukural-analytics` for the 20-minute check.

## Publish pack contents

`python studio.py publish-pack N` writes `episodes/KNNNN/publish/KNNNN_post.md` and `cover.py` makes `KNNNN_cover.jpg` (render with `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`). Cover: 1080x1920 story frame, red pill "குறள் N", title and hook text kept clear of faces. Description: 2 story lines, tag call to action, the kural, Tamil and English meanings, adhikaram and paal, hashtags, AI disclosure line. Instagram caption: hook with emoji, 2-line teaser, kural, tag line, hashtags.
