---
name: orukural-analytics
description: Check how a posted Orukural Orukadhai reel is performing on YouTube and Instagram, record the numbers in the episode retro, and propose lessons for the next scripts. Use after an episode is posted (about 20 minutes, next day, 3 days) or when Ananya asks for channel analytics.
---

# Orukural Orukadhai: analytics

Read-only. It never posts, comments, replies or changes any setting.

## Schedule per episode
About 20 minutes after posting, the next day, then about 3 days. Retention and swipe-away data take up to 2 days to appear.

## Sources (no screenshots needed)
- **Instagram: Windsor.ai `instagram` connector** (account `orukural.orukadhai`, id 17841432135396228). Call `get_fields` first, then `get_data` with `media_permalink, timestamp, media_caption, media_views, media_reach, media_like_count, media_comments_count, media_saved, media_shares, media_reel_avg_watch_time` (milliseconds) and `media_reel_skip_rate` (share of views skipped in the first 3 s), plus `media_reel_total_watch_time`. Account level: `reach_followers`, `reach_non_followers`, `views_followers`, `views_non_followers`, `follower_count_1d`, and audience country/age/gender fields. It does NOT give the second-by-second retention graph; use avg watch time and skip rate instead, and say so.
- **YouTube: Windsor.ai `youtube` connector** (account 64410, orukural.orukadhai1330@gmail.com). Call `get_fields` first for views, watch time, average view duration, likes, subscribers gained and traffic sources. Fall back to YouTube Studio in the built-in browser (Cmd+Shift+B) if a metric is missing.
- vidIQ is public data only for this account (`public_fallback`), so it gives no owner insights; use it only for competitor or trend research.
- Never type passwords. If Windsor reports an expired connection, ask Ananya to reconnect it.
- Match each Instagram row to its episode by permalink or caption (check `episode.yaml` links). If a permalink differs from the one recorded, flag it; do not assume.

## What to record
In `episodes/KNNNN/retro.md` under Analytics, with the check time: views, 3-second stay rate, average watch time and where viewers drop (K0301 dropped at about 12.7 s), likes, comments, saves, shares, subscribers, traffic split. Compare with the benchmarks: K0788 had 210 YouTube views, 4 likes and +1 subscriber in 20 minutes (95% Shorts feed); K0301 had 1,370 Instagram views and 16 YouTube views in 3 days.

## What to do with it
- Say plainly what the numbers show and what they cannot show. Do not invent missing figures.
- Compare hook type, length, relationship and ending style against earlier episodes.
- Propose edits to `data/lessons_learned.md` only from real evidence; she approves the edit. The file goes into every script prompt, so keep it short.
- Weekly summary (if asked): a table of all posted episodes with the same metrics and one recommendation.

## Weekly summary and next-reel suggestions

Runs every Monday morning IST (also on request). Save to `reports/weekly/YYYY-MM-DD.md` and email it to anusatheesh1905@gmail.com (see Delivery).

1. Table of every posted episode: posted date, YouTube views and average view duration, Instagram views, reach, skip rate, average watch time, likes, comments, saves, shares, new followers, traffic split. Mark figures that are too early to judge (under 48 hours old).
2. What the numbers show and what they cannot show. With only a handful of reels, say "small sample" instead of calling a trend.
3. **Next-reel suggestions**, each with evidence, effort and which part it touches: *script* (hook type, topic or bond, length, ending), *format* (cards, subtitles, music, pacing), *animation* (shot count, camera, clip length), *publishing* (title, caption, hashtags, cover, timing). Mark each "can do now" or "needs a pipeline or code change". Do not change style, templates or code from a suggestion: bring them to Ananya to discuss first.
4. Check the posted captions and titles against the pack for mistakes (wrong hashtags, missing AI disclosure, a different call to action).
5. A style-consolidation note: whether there is enough data yet to change the format. Not before roughly 8 to 10 posted reels unless one metric is clearly failing.
6. Append the accepted suggestions to `reports/weekly/suggestions.md`. The `orukural-orukadhai` preflight reads that file.

## Delivery
Send the report with the connected Gmail connector to anusatheesh1905@gmail.com only (never to anyone else). If sending fails, create a draft; if neither works, keep the file and tell Ananya. Do not open her mailbox in the browser.

**Email style (she reads it on a phone):** send an HTML email, never a plain-text dump. Pass `htmlBody` (full styled HTML) and a one-line `body` as the plain-text fallback. Copy the structure, colours and CSS of `email_example.html` in this folder: header banner, "At a glance" box, one card per reel with a 4-column stat grid (never a wide table), green for the best figure, a "Too early" pill for reels under 48 hours, the ideas grouped by script, format, animation and publishing, a highlighted caption check, and a style-change verdict. Keep it single column, max width 600px, explicit light colours on every container (so Gmail dark mode stays readable), with the Tamil text as written. Also save the same HTML as `reports/weekly/YYYY-MM-DD.html` next to the markdown file.

## Repo sync
After saving a weekly report or updating a retro, commit the text files (`reports/weekly/*`, `episodes/KNNNN/retro.md`) with a message such as `weekly analytics <date>` and push to `origin main` with `git pull --rebase` first, never force. If the push fails, keep the commit and tell Ananya. Do not commit `.env` or media.
