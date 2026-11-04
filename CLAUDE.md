# HASHKA VLOG EDIT

Mongolian podcast (politics, society, psychology) → edited episodes + regular 9:16 reels cut from them, with animated Mongolian captions.
User writes Mongolian (often Latin transliteration). Reply in Mongolian Cyrillic, short.
User is on Windows 11: use `python` (not `python3`) and give PowerShell commands, never brew/bash-only.

## Tools (all via one CLI)
`python scripts/edit.py <cmd> -h` (python3 on Mac/Linux) — cmds: info, frame, enhance, cutsilence, transcribe, srt2json, clip, render, reel, burn, podcast.
- Media in `input/`, intermediates in `work/<stem>/`, results in `output/`.
- Remotion project: `remotion/` (comps `Reel` 1080x1920, `Wide` 1920x1080, component `src/Edit.tsx`). Props come from edit.py; don't hand-edit `public/jobs/`.
- Fonts are local (`remotion/public/fonts`, Montserrat incl. cyrillic-ext for Ө/Ү). Never switch to Google Fonts CDN.

## Workflow
1. `podcast input/X.mp4` → clean audio, cut silence, `work/X_episode/transcript.txt` + `.srt`.
2. Find reel moments: read **transcript.txt only** (compact, timestamped). Pick 30–60 s self-contained moments with a strong hook in the first 3 s. Propose list: start–end, hook title, why.
3. `reel output/X_episode.mp4 --start mm:ss --end mm:ss --title "..." [--layout crop|blur|split --x 0.5]`.
   Always cut reels from the SAME file the transcript was made from (silence-cut changes timings). Its `work/<stem>/captions.json` is then sliced (no re-transcribe).
4. Check framing with `frame <video> --at <sec>` (one small image; only when needed).

## Caption accuracy (Whisper Mongolian is imperfect)
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
