# Lessons learned

The weekly analytics step rewrites the "From analytics" section from real numbers.
The script generator reads this whole file into every prompt, so keep it short and
concrete: what to do more of, what to stop.

## Starting rules (from the 25 Oct 2026 channel review)

- 45% of Instagram viewers swiped away in the first 3 seconds of Kural #001. Open on
  a tense moment or a direct question, never on a slow teaser or on the verse.
- Average watch was 6–10 s of a 1:31 video. Keep episodes 35–45 s.
- Zero saves and shares. End on one short lesson line that is worth screenshotting
  (no "save" text; an occasional "tag your <relation>" line is fine, not every reel).
- YouTube views came mostly from search: put the kural number and the key words of
  the verse in the title.

## From analytics

### K0301 (posted 27 Oct 2026, 45 s)

- The hook works: 82% of YouTube and 59% of Instagram viewers kept watching past 3 s.
- The average Instagram viewer left at about 12.7 s, long before the kural at 25 s. Put a
  one-line lesson teaser on screen at 10–12 s so they know where the story is going, and keep
  something happening every 2–3 s up to the kural.
- Zero saves, shares and comments. End on a short lesson card (no "save" text), ask one
  tag question (tag a friend, partner or sibling) instead of a general one, and make the
  story about a bond viewers want to send to someone.
- The 45 s cut works: keep 35–45 s.

## From episode reviews (K0788, K1330, K0100, K0467)

Story and script
- The kural's own image should be the story's image (K0788: a hand catching a slipping lungi), so the verse lands as the punchline.
- Angry or scolding lines: write "frowning, no smile". Flow adds smiles.
- Avoid a bare "கால்" (reads as "leg"); say "அழைப்பு". Write loanwords in Tamil script and check for stray non-Tamil letters: one bad character makes Gemini read the line about twice as slowly.
- Never end on a "next kural" teaser. Leave a deliberate silent beat as a gap between segments, with the shot spanning the same gap.
- Keep scripts to what fits 35–45 s, but plan Gemini at about 8 Tamil letters per second, not 11 (K0467 ran 48.9 s; K0785 and K1100 lines read about 1.5x longer than estimated). Keep short spoken lines under about 25 letters, and retime script.json to the real voice lengths before writing clip prompts: a clip's length is its line's slot plus 1 s, so one overlong line can push a 4 s clip to 8 s.

Voice and sync
- Make the voice before the clips and put the exact spoken line, in quotes, in each clip prompt. K0467 clips were made silent and again against the wrong audio, and lip sync forced a full remake.
- If Flow's mouth runs longer than the line, re-timing cannot fix it; use a slower take shaped by punctuation. Stay within 0.9–1.1× speed.

Flow prompts
- One master per recurring object and "exactly one <object>" (K0100 drew two kolams). Reference images steer more than prose.
- Say a person is INSIDE a room or glass wall (K0467 shots 2 and 8). Use a start frame already in motion if Flow closes a door the character must pass (K1330).
- Reference existing tiles by name and never re-upload PNGs. Download clips at 1080p Upscaled the first time.

Review
- Ananya's catches that self-review missed: two phones, a floating gate, phone at the chest, a frozen frame, a vanishing tumbler, a double arm-fold, smiling while scolding. Check these frame by frame before any cut.
