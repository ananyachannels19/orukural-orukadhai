# Flow jobs for K0301

Make each item in Google Flow and save it to `save_as` (paths are relative to the repo). Use the Flow project for adhikaram 31 (வெகுளாமை): https://flow.google.com/project/b7755f8b-6f52-4abf-8563-86ab7a09d09d

**Never generate the same thing twice.** Every job has a `flow_name`. Before generating, search the Flow project for an asset with that name (or the same prompt); if it exists, download it to `save_as` instead. Name each new generation with its `flow_name`. If Flow or the tool reports an error or timeout, look in the project first: Flow often finishes jobs that were reported as failed. Only then retry.

**Never wait idle.** While a job runs, check the Flow page every 30-60 s. A failed tile, or no progress after 2 min (image) or 4 min (clip), counts as a failure: look for a finished result, then retry up to 2 times. Post a one-line note after each finished clip. If Flow shows "unusual activity", stop and tell the user; never try to get around it.

**Clip frames come from the project.** For a clip's start (and any end) frame, pick the existing image tile in the Flow project (search or scroll the picker by flow name). Upload or generate only if it is truly missing, and then only once. **Delete failed tiles** (failed generations with no usable result); never delete a successful image or clip without the user's say-so.

**Log every job for the live dashboard:** `python studio.py event 301 <stage> <status> --shot N --attempt K --credits C --credits-left L --detail "..."`, with stage refs/images/image_check/clips/clip_check and status start/done/fail/retry/blocked. Log credits_left from Flow after every clip.

Work in this order:

1. **References** (characters, places, props). Made once; series ones are reused by every episode.
2. **Shot images**, attaching every listed reference image in the listed order.
3. **Image review.** Run `python studio.py continuity-sheet 301` and follow the continuity-review skill (`.claude/skills/continuity-review/SKILL.md`): compare every image with the references, redo any that drift (images are free), and mark each one `pass` in `episodes/K0301/continuity_review.json`. Do not start clips until every image passes; clips cost credits.
4. **Clips**, from the reviewed images. They need 0 credits over 0 day(s): 50 daily credits a day. Spend daily credits before monthly ones. Make only today's day number; if credits run out, stop and continue after the reset. Never buy credits.
5. **Clip review.** Run `continuity-sheet 301` again, check the first, middle and last frames of each clip, and mark clips `pass`. Redo a drifting clip only if credits allow; otherwise note it and tell the user.
6. Run `python studio.py visuals 301`, then `render 301`.
