"""Shared helpers: ffmpeg/ffprobe wrappers, paths, caption I/O."""
from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# Windows consoles/pipes default to cp1252 -> Cyrillic would crash prints
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IS_WIN = sys.platform == "win32"


def tool(name: str) -> str:
    """Resolve npx/npm to npx.cmd etc. on Windows."""
    return shutil.which(name) or name

ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "remotion"
WORK = ROOT / "work"
OUTPUT = ROOT / "output"


def run(cmd: list, quiet: bool = False, cwd: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    if not quiet:
        line = shlex.join(cmd)
        print("$", line[:160] + (" …" if len(line) > 160 else ""), flush=True)
    return subprocess.run(cmd, check=True, text=True, encoding="utf-8", errors="replace",
                          capture_output=quiet, cwd=cwd)


def ffmpeg(args: list, cwd: Path | None = None) -> None:
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostats", *args], cwd=cwd)


def probe(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", path], quiet=True).stdout
    data = json.loads(out)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    info = {"duration": float(data["format"]["duration"]),
            "has_audio": a is not None, "has_video": v is not None}
    if v:
        num, den = v.get("avg_frame_rate", "30/1").split("/")
        fps = float(num) / float(den) if float(den) else 30.0
        rot = 0
        for sd in v.get("side_data_list", []):
            rot = int(sd.get("rotation", 0)) or rot
        w, h = int(v["width"]), int(v["height"])
        if abs(rot) in (90, 270):
            w, h = h, w
        info.update(width=w, height=h, fps=round(fps, 3))
    return info


def stem_dir(src: Path) -> Path:
    d = WORK / src.stem
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------- time formatting ----------

def srt_time(ms: float) -> str:
    ms = max(0, int(round(ms)))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse_srt_time(t: str) -> int:
    hms, ms = t.strip().replace(".", ",").split(",")
    h, m, s = hms.split(":")
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def short_time(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m):02}:{s:04.1f}"
