"""Caption utilities. Caption format = Remotion `Caption` type:
{text, startMs, endMs, timestampMs, confidence, pageBreakAfter?}
`text` keeps a leading space before each word (Remotion is whitespace-sensitive).
"""
from __future__ import annotations

import re
from pathlib import Path

from common import parse_srt_time, short_time, srt_time

PUNCT_END = re.compile(r"[.!?…]$")


def group_lines(words: list[dict], max_chars: int = 32, max_ms: int = 2600,
                gap_ms: int = 600) -> list[list[dict]]:
    """Split words into readable subtitle lines."""
    lines, cur = [], []
    for w in words:
        if cur:
            text_len = len("".join(x["text"] for x in cur).strip()) + len(w["text"])
            too_long = text_len > max_chars or w["endMs"] - cur[0]["startMs"] > max_ms
            gap = w["startMs"] - cur[-1]["endMs"] > gap_ms
            sentence_end = PUNCT_END.search(cur[-1]["text"].strip()) is not None
            if too_long or gap or sentence_end or cur[-1].get("pageBreakAfter"):
                lines.append(cur)
                cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def words_to_srt(words: list[dict], **kw) -> str:
    out = []
    for i, line in enumerate(group_lines(words, **kw), 1):
        text = "".join(w["text"] for w in line).strip()
        out.append(f"{i}\n{srt_time(line[0]['startMs'])} --> {srt_time(line[-1]['endMs'])}\n{text}\n")
    return "\n".join(out)


def parse_srt(text: str) -> list[dict]:
    cues = []
    for block in re.split(r"\n\s*\n", text.strip().replace("\r", "")):
        lines = [l for l in block.split("\n") if l.strip()]
        idx = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if idx is None:
            continue
        a, b = lines[idx].split("-->")
        cues.append({"startMs": parse_srt_time(a), "endMs": parse_srt_time(b),
                     "text": " ".join(lines[idx + 1:]).strip()})
    return cues


def srt_to_captions(text: str) -> list[dict]:
    """Rebuild word-level captions from (hand-corrected) SRT.
    Word timings are spread across each cue proportionally to word length."""
    caps = []
    for cue in parse_srt(text):
        words = cue["text"].split()
        if not words:
            continue
        total = sum(len(w) + 1 for w in words)
        dur = cue["endMs"] - cue["startMs"]
        t = cue["startMs"]
        for i, w in enumerate(words):
            d = dur * (len(w) + 1) / total
            caps.append({"text": (" " if caps else "") + w, "startMs": round(t),
                         "endMs": round(t + d), "timestampMs": round(t + d / 2),
                         "confidence": None,
                         **({"pageBreakAfter": True} if i == len(words) - 1 else {})})
            t += d
    return caps


def slice_captions(caps: list[dict], start_s: float, end_s: float) -> list[dict]:
    """Keep captions inside [start, end] and shift them to start at 0."""
    s, e = start_s * 1000, end_s * 1000
    out = []
    for c in caps:
        if c["endMs"] <= s or c["startMs"] >= e:
            continue
        n = dict(c)
        n["startMs"] = max(0, round(c["startMs"] - s))
        n["endMs"] = round(min(c["endMs"], e) - s)
        if c.get("timestampMs") is not None:
            n["timestampMs"] = round(min(max(c["timestampMs"] - s, n["startMs"]), n["endMs"]))
        out.append(n)
    if out:
        out[0]["text"] = out[0]["text"].lstrip()
    return out


def compact_transcript(caps: list[dict]) -> str:
    """Token-cheap transcript for Claude: one line per sentence with [mm:ss.s]."""
    out = []
    for line in group_lines(caps, max_chars=140, max_ms=15000, gap_ms=1200):
        text = "".join(w["text"] for w in line).strip()
        out.append(f"[{short_time(line[0]['startMs'] / 1000)}-{short_time(line[-1]['endMs'] / 1000)}] {text}")
    return "\n".join(out)


def apply_fixes(caps: list[dict], fixes: dict[str, str]) -> list[dict]:
    """Replace commonly mis-heard words (dictionary.txt: `буруу => зөв`)."""
    if not fixes:
        return caps
    for c in caps:
        core = c["text"].strip()
        key = core.lower().strip(".,!?…")
        if key in fixes:
            lead = c["text"][: len(c["text"]) - len(c["text"].lstrip())]
            tail = core[len(core.rstrip(".,!?…")):]
            c["text"] = lead + fixes[key] + tail
    return caps


def load_fixes(path: Path) -> dict[str, str]:
    fixes = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=>" in line and not line.lstrip().startswith("#"):
                a, b = line.split("=>", 1)
                fixes[a.strip().lower()] = b.strip()
    return fixes
