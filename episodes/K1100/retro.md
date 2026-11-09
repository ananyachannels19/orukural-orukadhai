# K1100 retro: வளையல் பிடிக்காதுன்னு சொன்னவ (The woman who said she hated bangles)

- Kural / adhikaram / bond: #1100 கண்ணொடு கண்இணை நோக்கொக்கின் (110 குறிப்பறிதல், Recognition of the Signs) / couple (Naveen and Dharani, married; no third character). Gates passed 9 Nov 2026: script, shots, clips, draft. Final built; not posted.
- Flow account and project: Revathi Satheesh (`revathisatheesh2604@gmail.com`, chosen by Ananya; the second account's tab was not signed in), project `5b659660-6343-4f3c-a6cd-14151e60c0da` ("K1100 – Bangle stall"). All Flow work in Chrome with the Claude in Chrome tools.
- Credits: planned 74 / used 74 (no remakes). One attempt (shot 3) was refused by Flow and refunded, so it cost nothing. Images, voice and assembly cost 0.
- Hook type used and where viewers dropped (when analytics exist): surprising_line ("எனக்கு வளையலே பிடிக்காது!"). No analytics yet.

## Prompts that worked
- Shot 4 (silent first 3.4 s, then one line to camera): "From 0 s to 3.4 s nobody on screen talks ... says this line aloud once only ... After the line both stay silent." Speech landed at 3.8 s and the line came once, with Naveen's mouth closed.
- Shots 2 and 3: "For the first three seconds nobody speaks" plus the exact line in quotes; speech began at 3.5 s and 3.8 s as asked.
- Shot 6 and 7 (silent beats): "every mouth stays closed ... no voice or speech is heard" kept shot 6 silent (-56 dB).
- Image stage: "face turned towards the camera, both eyes visible, not in profile", "exactly one set of green bangles ... firmly attached to a peg; nothing floats in the air" fixed profile faces and a floating bangle set.

## Prompts that failed, and the fix
- Shot 3 clip from a tight close-up of Dharani: Flow refused it as "harmful content related to minors" (a false positive: big eyes, close-up framing on a 26-year-old). Refunded. Fix: a waist-up still, "a clearly adult woman in her late twenties", and "Dharani, a grown woman" in the clip prompt. It then passed.
- Shot 2 clip: Flow burned a garbled "Dharani" caption into the lower-right corner from about 1 s even though the prompt said "No on-screen text". Fixed in assembly with a blur box in edit.json (shot 2). Later prompts added "no captions, no subtitles, no name labels, no watermarks"; shots 3 to 7 had none.
- Shot 3 clip: Flow repeated "வீட்டுக்கு போலாம்" after the line. Fixed by pinning the real speech spans in lipsync.json and by the cut ending before the repeat.
- Shot 7 clip: a second green bangle set appeared on Dharani's other wrist from about 2.5 s, plus stray voice and laughter. Ananya accepted the bangles; the voice was muted (original kept in clips/original/).
- Images: shot 2 first redo had a floating green bangle set; shot 4 first redo changed Naveen's checked shirt to plain grey and had a foreground rail; shot 1 to 4 first attempts had speaking characters in profile. All fixed with free redos.

## Ananya's review notes
- Gate 1 (script), Gate 2 (shots), Gate 3 (clips, with the shot 2 patch and shot 7 accepted) and Gate 4 (draft) were approved without further notes. Nothing timestamped yet.
- Shot 7's second bangle set and shot 2's corner caption were caught by my own clip review before she saw them.

## Voice and sync issues
- 12 Gemini TTS requests: key 1 made lines 1 to 10 (10 requests), key 2 made lines 8 and 11 with Ananya's go-ahead. Line 8 was made twice (the first wording was too long for a 4 s clip).
- Gemini read about 1.5x slower than the 11 letters/s estimate: every line came out longer than "text needs" (e.g. the 25-letter hook 2.1 s against 1.2 s). The kural line was 8.64 s in an 8.0 s slot.
- Naveen's line 8 and the narrator's line 11 measured 184 Hz and 165 Hz (above the male range and the other narrator lines). The delivery notes were "warm, proud" and "inviting". Not yet confirmed by ear.
- Assembly fit: hook 1.07x; shot 2 1.18x and 1.05x; shot 3 1.00x and 0.90x; shot 4 0.89x and 0.80x (capped); shot 5 1.10x.
- The clip length is the line's slot plus 1.0 s, not the voice length: Naveen's 3.4 s slot made shot 5 an 8 s clip (79 credits) until I shortened the line.

## Process mistakes (time or credits lost)
- Renaming tiles in the Flow viewer by filmstrip position sent three names to the wrong images (the approved shot 1 was named x_old_shot02_profile). Caught before any wrong start frame was used. Check the tile after a rename, or rename from the grid.
- The retime had to be done by hand after the voice, because Gemini's real lengths differ from the plan. Better to estimate at 8 letters/s and keep a 4 s slot per short line.
- `studio.py voice-ab` and `visuals` both need `visuals.json`; run `visuals` first.
- `assemble` accepts only the exact string "pass" in continuity_review.json; keep notes in the "notes" field.
- The long verse (kural 1100 line 1) overflowed the frame at the smallest size and was clipped. Fixed in `orukural/signature.py` (shrink further, only when it overflows); 67 tests pass. Found in my own draft QC before Ananya saw it.
- The publish pack repeated the tag question in the Instagram caption (the script's caption already ended with it). Removed from caption_ta.
- Cover text: avoided the pre-base vowels (ெ ே ை ொ ோ ௌ) because this Python has no Raqm: "கண்ணும் கண்ணும் / புரிஞ்சிடும்".

## Analytics
(~20 min, next day, later) Not posted yet.

## Proposed lessons for data/lessons_learned.md
(only if repeated in 2+ episodes or Ananya confirmed; she approves the edit)
- Repeated in K0785 and K1100: Gemini reads Tamil slower than 11 letters/s (about 8) and the clip length is slot + 1 s. Proposed line: "Plan 8 Tamil letters per second, keep short lines under 25 letters, and retime script.json to the real voice lengths before the clip prompts."
- Candidates to watch (one episode so far): a tight close-up of an adult woman with big eyes can be refused as a minors-content false positive (use waist-up, "a grown woman"); Flow may burn a name caption into a speaking shot even with "no on-screen text", so say "no captions, no name labels" in every clip prompt.
