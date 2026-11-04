# HASHKA VLOG EDIT

Mongolian podcast (politics, society, psychology) → edited episodes + regular 9:16 reels cut from them, with animated Mongolian captions.
User writes Mongolian (often Latin transliteration). Reply in Mongolian Cyrillic, short.
User is on Windows 11: use `python` (not `python3`) and give PowerShell commands, never brew/bash-only.

## Tools (all via one CLI)
`python scripts/edit.py <cmd> -h` (python3 on Mac/Linux) — cmds: info, frame, enhance, cutsilence, transcribe, srt2json, clip, render, reel, burn, podcast.
- Media in `input/`, intermediates in `work/<stem>/`, results in `output/`.
- Remotion project: `remotion/` (comps `Reel` 1080x1920, `Wide` 1920x1080, component `src/Edit.tsx`). Props come from edit.py; don't hand-edit `public/jobs/`.
- Fonts are local (`remotion/public/fonts`, Montserrat incl. cyrillic-ext for Ө/Ү). Never switch to Google Fonts CDN.

## Cloud sessions (claude.ai/code) — user's main way of working
- Fresh machine each session: if `remotion/node_modules` is missing, run `./cloud-setup.sh` first.
- Get video: user shares a Google Drive/Dropbox link → `python3 scripts/edit.py fetch "<link>" --name ep12.mp4` (never ask them to attach video in chat or commit it).
- Deliver: send finished files from `output/` with SendUserFile (reels mp4, .srt, _youtube.md). Full episodes are huge: send SRT/text unless asked.
- Machine is reclaimed when idle and media is not in git: finish + deliver in the same session.
- 4 CPU, no GPU: full-episode large-v3 is slow (~1–2× real time). For reels when the user gives times, transcribe only the clip.

## PRO reel (noorog-style) — preferred for 16:9 podcast clips
`pro input/X.mp4 [--start --end] --elements els.json --title "hook" [--shots shots.json]`
- Face-tracked 9:16 crop per shot + person cut-out layer (graphics go BEHIND the speaker).
- Check `work/X/X_pro_*/shots.json`: in wide/split shots set `x` to the **speaking** person (biggest face is not always the speaker), `zoom` 1.3 for wide shots. Verify with 1 small contact-sheet image.
- Elements (source seconds; sync `from` to the spoken word's time in captions.json): `bigword` (key phrase, front, hides captions), `counter` (numbers), `gauge` (percent), `list` (+`times` per item), `sticker` (image/icon behind speaker, `label`), `timeline` (points {label, at, text} appear when spoken).
- Giant title behind the head: `bigword` with `layer:"back"`, `y:0.17`, `size:190`; `*word*` = accent colour, rest white.
- Every element starts exactly at the spoken word's `startMs` (look it up in captions.json for that range only).
- Images: `python3 scripts/images.py "<english query>" --name x` (Wikimedia Commons, free licences, credits in images/CREDITS.txt). Prefer transparent PNG for cut-outs.
- Rhythm: one visual every 3–6 s, never two big things at once, hook in first 3 s.

## Workflow
1. `podcast input/X.mp4` → clean audio, cut silence, `work/X_episode/transcript.txt` + `.srt`.
0. **Main use: ~1-minute reels.** Short phone video (already a reel) → `reel input/X.mp4 --tight --title "..."` (whole video, pauses removed). Keep reels ≤ 60 s.
2. Find reel moments: read **transcript.txt only** (compact, timestamped). Pick 45–60 s self-contained moments with a strong hook in the first 3 s. Propose list: start–end, hook title, why.
3. `reel output/X_episode.mp4 --start mm:ss --end mm:ss --title "..." [--layout crop|blur|split --x 0.5]`.
   Quality path: add `--no-render`, fix the printed captions.srt, `srt2json`, then `render <clip>`.
   Always cut reels from the SAME file the transcript was made from (silence-cut changes timings). Its `work/<stem>/captions.json` is then sliced (no re-transcribe).
4. Check framing with `frame <video> --at <sec>` (one small image; only when needed).

## Caption accuracy (Whisper Mongolian is imperfect)
- Default model `mn` = Mongolian fine-tuned turbo (`setup-mn` once); fallback `mn-small`. Stock large-v3 is bad for mn — don't use.
- Unclear parts: re-run that range with both models and merge; never guess political statements.
- Fix text in `work/<stem>/captions.srt` (keep timings), then `srt2json` → captions.json.
- Recurring mistakes → add to `config/dictionary.txt` (`буруу => зөв`). Domain words → `config/whisper_prompt.txt`.
- Keep meaning exact; never invent words. Political content: never cut a quote so it changes what the speaker meant; spell names/parties/institutions correctly.

## Token rules
- Never read: media, `*.wav`, `captions.json` of long files, `node_modules`, `package-lock.json`. Use transcript.txt / `info`.
- Don't view many frames; 1–2 at width 360–480.
- Long renders: run in background, don't poll output repeatedly.
- See TOKEN-SAVING.md.

## Quality defaults
Reels −14 LUFS, episodes −16 LUFS, H.264 CRF 18, 30 fps, AAC 192k. Caption safe zone: y≈0.68 (above IG/TikTok UI).
