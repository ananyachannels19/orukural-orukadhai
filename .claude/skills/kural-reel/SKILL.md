---
name: kural-reel
description: Make, review, render and post a Thirukkural story reel (Oru Kural Oru Kadhai) for YouTube Shorts and Instagram with the orukural-studio pipeline and Google Flow.
---

# Kural reel: end-to-end workflow

This skill is for one episode (e.g. K0788) going from script to live posts on YouTube Shorts and Instagram Reels. It holds every rule and lesson learned on K0001, K0301 and K0788.

The repo is `orukural-studio` on Ananya's Mac (`/Users/ananya-24962/Documents/orukural-studio`).
- Tools: `studio.py` (`assemble`, `assemble --final`, `publish-pack`, `live`, `flow-progress`, `voice-ab`), the `orukural/` modules and `config.yaml`.
- Keep the tests passing (`pytest`).

## Standing rules (never break)

1. **No "next kural" teaser** (அடுத்த குறள்) at the end of any video or caption. Never promise dates or a schedule to viewers.
2. **Approve images before video.** Show Ananya the generated stills and get her OK before any Flow clip video is made.
3. **Don't waste free voice requests.** Gemini TTS free tier = 10 requests a day, reset at 12:30 IST. No test takes "just to compare".
4. **Flow account:** use only the new account (u/2, about 1,000 credits). Don't use the old account, and don't automate across several Gmail accounts.
5. **Posting is irreversible.** Post only after Ananya's clear go-ahead. A message ending in "?" is a question, not a go-ahead. Post once per platform, and check first that the episode isn't already up.
6. **Monitor proactively.** Long jobs must send a progress note every 2–3 minutes, and renders run in the background. Don't make her ask "update?".
7. **Flow 1080p upscale and download are free** (0 credits). Always use the 1080p clips for the final.

## 1. Script

- Story in spoken Tamil, with the kural, the Tamil meaning and the English meaning checked against `data/kurals.json`.
- **Avoid words that read wrong in English-ish Tamil**, e.g. a bare "கால்" (reads as "leg"). Say "அழைப்பு" instead. `schema.py` script-check warns on a bare கால் (`test_bare_kaal_is_flagged`).
- The narrator voice is Charon (Gemini 3.8 flash TTS). The model doesn't take delivery notes or system instructions; it reads them aloud. Shape delivery only with punctuation (commas, ellipses, "!", "?").

## 2. Images and clips (Google Flow)

- Flow is driven through flow-mcp: Chrome profile `~/.flow-mcp/chrome-profile` on debug port 9333, and the Flow Studio dashboard at http://127.0.0.1:8787 (`node dist/studio.js`). If 8787 dies, restart it standalone and resubmit the lost items.
- Reference images steer more than the prompt does. If the reference shows a brown door, the character will hold a brown door even if the prompt says "green gate". Fix the reference image, not just the prompt.
- Watch for continuity bugs:
  - two phones in one hand
  - a gate or object floating in the air
  - props such as cups changing between shots
  - wrong hand or prop colour
- Retrying a clip costs about 12 credits. Ask before retrying.
- Download every clip at 1080p into `episodes/<K>/clips/`, keep the 720p originals in `clips/720/`, and move old takes to `clips/v1_before_<date>/`.

## 3. Review checklist (run on every cut, before showing her)

- **Phone and props:** the phone is at the ear while the character talks on a call, not on the chest.
- **Lip sync:** no silent mouth movement, and no line spoken with a closed mouth.
- **Frozen frames:** run ffmpeg `freezedetect` and `mpdecimate`. The render must fail on any held frame over 0.3 s.
  - Don't let lip-sync push a clip past its end. If a clip is too short, slow it down rather than freeze it.
  - Match the colour metadata on stills, because a mismatch shows up as a freeze.
- **Dialogue timing:** each line lands on its action, so no late lines (the K0788 "lungi" line was late). Watch for small breaths pushing lines late (a 0.17 s breath did that).
- **Loop:** the ending must not repeat the hook line ("மூச்சு விட முடியல" came back at 39 s in v4).
- **Subtitles:** narrator and dialogue subtitles never show at the same moment.
- Transcribe the final with whisper.cpp and compare it word for word with the script.
- List the remaining small flaws and let Ananya decide which to accept.

## 4. Style defaults (picked on K0788)

- **Hook card H2:** a typed timestamp like "3:04 AM", with a short line under it (e.g. "ஒரு அழைப்பு."). It must not look like a subtitle.
- **Karaoke subtitles** for dialogue, with no grey or black background strip: outline and shadow only.
- **Narrator subtitles** in yellow italic, clearly different from dialogue.
- **Question and answer cards** handwritten in the Kavivanar font (`assets/fonts/Kavivanar-Regular.ttf`, OFL), e.g. "கூப்பிடும் முன்னே வருபவன் யார்?" and "கூப்பிடாமலே வருபவன் தான் நண்பன்".
- **Ending:** a narrator line asking viewers to tag a friend, e.g. "அப்படிப்பட்ட உங்க ஃப்ரெண்ட்-அ டேக் பண்ணுங்க!". No "சேவ் பண்ணுங்க" (save) text, and no teaser.

## 5. Final render

- `studio.py assemble --final` at 1080×1920, 30 fps, x264 CRF 15, slow preset, AAC 320k.
- Two-pass loudnorm to −14 LUFS, true peak −1 dBTP.
- Output: `review/<K>/<K>_final_1080src.mp4`. Keep the previous final as `_v1` before overwriting.
- Commit code changes with clear messages. Leave unrelated uncommitted data files alone.

## 6. Publish pack

`studio.py publish-pack` writes `episodes/<K>/publish/<K>_post.md`, and `cover.py` makes `<K>_cover.jpg`.

**Cover:** 1080×1920, a story still, a red pill "குறள் N", a yellow title line and a white hook line.

**Pack contents:**
- YouTube title: `குறள் N | <hook> | Thirukkural Story #Shorts`
- YouTube description:
  - 2 story lines
  - the tag call to action
  - 📜 the kural
  - the Tamil and English meaning
  - 📖 the adhikaram and paal
  - 5 hashtags
  - the AI disclosure line
- Tags
- Pinned comment (the tag call to action)
- Instagram caption: hook, story, kural, call to action, hashtags

Check before posting:
- no schedule lines, no 🔔, no teaser
- the kural matches `kurals.json`
- no duplicate lines

The usual slot is 7:00–7:30 pm IST, but post now if she says now.

## 7. Posting (Claude desktop app's built-in browser on her Mac)

1. Get her explicit go-ahead (now or a time).
2. Check that YouTube Studio and the Instagram profile don't already have the episode.
3. **Sign-in hand-off:** if either platform is signed out, ask her to open the browser pane (Cmd+Shift+B), sign in to the Google account that owns the channel and to Instagram (orukural.orukadhai), and reply "signed in". Never type passwords.
4. **File picks are hers.** The browser can't attach files. Open the upload box, have Finder show the file selected, and ask her to drag it in or pick it:
   - the video for YouTube ("picked")
   - the thumbnail ("thumb")
   - the video for Instagram ("ig picked")
   - the Instagram cover ("cover")
5. **YouTube:**
   - pack title, description and tags
   - the cover as thumbnail
   - Not made for kids
   - Altered/synthetic content = Yes
   - Public
   - leave the tab alone until the upload hits 100%, then Publish
6. **Instagram:**
   - Original 9:16 crop
   - the cover
   - the caption pasted unchanged
   - AI label ON (check that "AI content" shows)
   - Share once; "Sharing…" can take about 2 minutes
7. Send her both live URLs.
8. Pinned comment: post it once if she approves. Pinning needs a one-time YouTube advanced-features verification (a video selfie or ID, which only she can do). Never start or submit it for her.

## 8. Analytics

- First check about 20 minutes after posting, then the next day. Retention and swipe-away data take up to 2 days.
- Read YouTube Studio for views, likes, subscribers, traffic sources (the Shorts feed share is the key signal) and the comparison with earlier Shorts.
- Full Instagram insights (reach, saves, shares, watch time) are only in the Instagram app. Studio charts don't load while the browser pane is hidden.
- K0788 benchmark: 210 views, 4 likes and +1 subscriber in 20 minutes, 95% from the Shorts feed (K0301: 16 views in 3 days on YouTube, 1,370 on Instagram).

## Working with the Mac session

- Ask for a note every 2–3 minutes. If it goes silent for over 10 minutes, check its status before restarting it. A restarted session may find the old one already finished, so check the outputs first.
- Usage-limit or connection errors: report them and resume. Don't redo finished work.
- Say exactly what is on screen. Never claim a window is "in front" unless you checked.
