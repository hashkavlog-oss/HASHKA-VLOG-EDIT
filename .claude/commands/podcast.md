---
description: Бүтэн podcast дугаар засах (дуу, чимээгүй хасах, монгол SRT)
argument-hint: <input видео>
---
Edit full episode: $ARGUMENTS

1. `python scripts/edit.py podcast <input>` (run in background; it prints only every 10%).
2. When done, read `work/<stem>_episode/transcript.txt` and write in Mongolian:
   - YouTube title (3 variants), description (≤ 120 words), chapters `00:00 Гарчиг` list.
   - 3–5 reel candidates (start–end + hook).
3. Save that text to `output/<stem>_youtube.md`. Report paths.
