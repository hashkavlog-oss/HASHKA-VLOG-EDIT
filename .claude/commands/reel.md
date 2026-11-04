---
description: Podcast видеоноос reel хийх (сэдэв/хугацаа өгч болно)
argument-hint: <input видео> [хүсэлт]
---
Make reels from: $ARGUMENTS

0. If `output/<stem>_episode.mp4` exists (made by /podcast), use it as input instead of the raw file — timestamps in its transcript match it.
1. If `work/<stem>/transcript.txt` is missing, run `python scripts/edit.py transcribe <input>` (background, wait for finish).
2. Read only transcript.txt. Propose 3–5 reel moments (30–60 s): start–end, Mongolian hook title (≤ 7 words), one-line reason. Wait for user choice.
3. Render each chosen one with `python scripts/edit.py reel ...`. Use `--layout split` if two speakers side by side; check one frame first if unsure.
4. Report output paths only.
