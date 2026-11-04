---
description: Монгол субтитрийн алдааг засах
argument-hint: <work/<stem> хавтас>
---
Fix Mongolian captions in $ARGUMENTS/captions.srt:
- Correct spelling/grammar of Whisper mistakes; keep every timing line and cue count unchanged.
- Don't paraphrase; keep the speaker's words. Edit in chunks (Edit tool), don't rewrite the whole file at once if it's long.
- Then run `python scripts/edit.py srt2json $ARGUMENTS/captions.srt`.
- Add repeated mistakes to `config/dictionary.txt`.
