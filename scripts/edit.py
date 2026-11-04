#!/usr/bin/env python3
"""HASHKA VLOG EDIT – podcast & reels pipeline (ffmpeg + faster-whisper + Remotion).

Run `python3 scripts/edit.py -h` or `python3 scripts/edit.py <command> -h`.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from captions import (apply_fixes, auto_pops, compact_transcript, load_fixes,  # noqa: E402
                      slice_captions, srt_to_captions, words_to_srt)
from common import (OUTPUT, REMOTION, ROOT, ffmpeg, load_json, probe,  # noqa: E402
                    save_json, stem_dir, tool)

VIDEO_OUT = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]

# Voice chain: rumble cut -> denoise -> de-ess-ish lowpass -> compressor -> loudness
def voice_chain(lufs: float = -14, denoise: bool = True) -> str:
    parts = ["highpass=f=80", "lowpass=f=14000"]
    if denoise:
        parts.append("afftdn=nf=-25")
    parts += ["acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2",
              f"loudnorm=I={lufs}:TP=-1.5:LRA=9"]
    return ",".join(parts)


def tc(value: str) -> float:
    """'83.5', '1:23.5' or '0:01:23.5' -> seconds."""
    sec = 0.0
    for p in str(value).split(":"):
        sec = sec * 60 + float(p)
    return sec


def out_path(arg: str | None, src: Path, suffix: str) -> Path:
    p = Path(arg) if arg else OUTPUT / f"{src.stem}_{suffix}.mp4"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- info / frame
def cmd_fetch(a):
    """Download a video into input/ from a Google Drive / Dropbox / direct link (for cloud sessions)."""
    url = a.input
    dest_dir = ROOT / "input"
    dest_dir.mkdir(exist_ok=True)
    if "drive.google.com" in url or "docs.google.com" in url:
        import gdown
        if "/folders/" in url:
            paths = gdown.download_folder(url, output=str(dest_dir), quiet=True)
            for f in paths or []:
                print("✔", f)
            return
        out = gdown.download(url, output=str(dest_dir) + "/", quiet=True, fuzzy=True)
        if not out:
            raise SystemExit("Татаж чадсангүй. Drive дээр 'Anyone with the link' болгосон эсэхээ шалгаарай.")
        out = Path(out)
    else:
        if "dropbox.com" in url:
            url = url.replace("dl=0", "dl=1") if "dl=0" in url else url + ("&" if "?" in url else "?") + "dl=1"
        name = a.name or Path(url.split("?")[0]).name or "video.mp4"
        out = dest_dir / name
        subprocess.run(["curl", "-L", "--fail", "-sS", "-o", str(out), url], check=True)
    if a.name and out.name != a.name:
        out = out.rename(dest_dir / a.name)
    info = probe(out)
    print(f"✔ {out}  ({out.stat().st_size / 1e6:.0f} MB, {info['duration'] / 60:.1f} мин,"
          f" {info.get('width')}x{info.get('height')})")


def cmd_info(a):
    print(json.dumps(probe(Path(a.input)), indent=1))


def cmd_frame(a):
    """Save small JPG frames so Claude can look at framing (images cost tokens!)."""
    src = Path(a.input)
    d = stem_dir(src) / "frames"
    d.mkdir(exist_ok=True)
    for t in a.at:
        out = d / f"frame_{tc(t):08.2f}.jpg"
        ffmpeg(["-ss", tc(t), "-i", src, "-frames:v", "1", "-vf", f"scale={a.width}:-2",
                "-q:v", "4", out])
        print(out)


# ---------------------------------------------------------------- audio
def cmd_enhance(a):
    src = Path(a.input)
    out = out_path(a.output, src, "clean")
    has_video = probe(src)["has_video"]
    vcodec = ["-c:v", "copy"] if has_video else ["-vn"]
    ffmpeg(["-i", src, "-af", voice_chain(a.lufs, not a.no_denoise), *vcodec,
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out])
    print("✔", out)


def detect_silence(src: Path, noise: str, min_dur: float) -> list[tuple[float, float]]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af",
                        f"silencedetect=noise={noise}:d={min_dur}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def cmd_cutsilence(a):
    src = Path(a.input)
    info = probe(src)
    dur = info["duration"]
    silences = detect_silence(src, a.noise, a.min)
    keep, cur = [], 0.0
    for s, e in silences:
        e = dur if e is None else e
        cut_a, cut_b = s + a.pad, e - a.pad
        if cut_b - cut_a > 0.05:
            if cut_a > cur:
                keep.append((cur, cut_a))
            cur = cut_b
    if cur < dur:
        keep.append((cur, dur))
    removed = dur - sum(b - x for x, b in keep)
    print(f"Чимээгүй хэсэг: {len(silences)} ширхэг, {removed:.1f}s хасна ({dur:.1f}s → {dur - removed:.1f}s)")
    work = stem_dir(src)
    save_json(work / "cutlist.json", keep)
    if a.dry_run:
        return
    v = info["has_video"]
    lines = []
    for i, (x, b) in enumerate(keep):
        if v:
            lines.append(f"[0:v]trim={x:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];")
        lines.append(f"[0:a]atrim={x:.3f}:{b:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.01,afade=t=out:st={max(0, b - x - 0.01):.3f}:d=0.01[a{i}];")
    ins = "".join((f"[v{i}]" if v else "") + f"[a{i}]" for i in range(len(keep)))
    lines.append(f"{ins}concat=n={len(keep)}:v={int(v)}:a=1" + ("[v][a]" if v else "[a]"))
    script = work / "cut_filter.txt"
    script.write_text("\n".join(lines))
    out = out_path(a.output, src, "cut")
    maps = ["-map", "[v]", "-map", "[a]"] if v else ["-map", "[a]"]
    ffmpeg(["-i", src, "-filter_complex_script", script, *maps, *VIDEO_OUT, out])
    print("✔", out)


# ---------------------------------------------------------------- transcription
def transcribe(src: Path, model_name: str, prompt: str | None) -> list[dict]:
    import numpy as np
    # Decode with ffmpeg ourselves (avoids PyAV version issues): 16 kHz mono float32
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(src), "-vn",
                          "-ac", "1", "-ar", "16000", "-af", "highpass=f=80",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    try:
        import ctranslate2
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    except Exception:
        device = "cpu"
    if device == "cuda":
        try:
            return _transcribe(audio, model_name, prompt, "cuda")
        except Exception as e:  # e.g. cublas64_12.dll missing on Windows
            print(f"GPU ажиллахгүй байна ({str(e)[:80]}), CPU руу шилжлээ.")
    return _transcribe(audio, model_name, prompt, "cpu")


MODEL_ALIASES = {
    # Mongolian fine-tuned models (much better than stock Whisper for mn)
    "mn": "models/mn-turbo",            # Tsedee/whisper-large-v3-turbo-mn-2 → CT2 (python scripts/edit.py setup-mn)
    "mn-small": "sonsyo/sonsyo-whisper-mn-ct2",
}


def resolve_model(name: str) -> str:
    name = MODEL_ALIASES.get(name, name)
    if name.startswith("models/"):
        if not (ROOT / name / "model.bin").exists():
            print("⚠ models/mn-turbo алга (`setup-mn` ажиллуул). mn-small ашиглаж байна.")
            return MODEL_ALIASES["mn-small"]
        return str(ROOT / name)
    return name


def cmd_setup_mn(a):
    """Download + convert the Mongolian turbo Whisper to CTranslate2 (one time, ~1.6 GB)."""
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers", "torch",
                    "--extra-index-url", "https://download.pytorch.org/whl/cpu"], check=True)
    subprocess.run(["ct2-transformers-converter", "--model", "Tsedee/whisper-large-v3-turbo-mn-2",
                    "--output_dir", str(ROOT / "models" / "mn-turbo"), "--quantization", "int8",
                    "--copy_files", "tokenizer.json", "preprocessor_config.json", "--force"], check=True)
    print("✔ models/mn-turbo")


def _transcribe(audio, model_name: str, prompt: str | None, device: str) -> list[dict]:
    from faster_whisper import WhisperModel
    model_name = resolve_model(model_name)
    compute = "float16" if device == "cuda" else "int8"
    print(f"Whisper '{model_name}' ({device}/{compute}) ачаалж байна…", flush=True)
    model = WhisperModel(model_name, device=device, compute_type=compute)
    # Silero VAD drops real (quiet / overlapping) Mongolian speech, so only use it on long files
    long_file = len(audio) / 16000 > 600
    segments, info = model.transcribe(
        audio, language="mn", word_timestamps=True, vad_filter=long_file,
        vad_parameters={"min_silence_duration_ms": 1000, "threshold": 0.25}, beam_size=5,
        initial_prompt=prompt, condition_on_previous_text=False)
    caps, t0, next_pct = [], time.time(), 10
    for seg in segments:
        # hallucination guard: silent/garbage segments
        if seg.no_speech_prob > 0.6 and seg.avg_logprob < -0.8:
            continue
        if seg.avg_logprob < -1.2 or seg.compression_ratio > 2.6:
            continue
        words = seg.words or []
        for i, w in enumerate(words):
            text = w.word if caps else w.word.lstrip()
            if not text.strip():
                continue
            caps.append({"text": text, "startMs": round(w.start * 1000),
                         "endMs": round(w.end * 1000),
                         "timestampMs": round((w.start + w.end) * 500),
                         "confidence": round(w.probability, 3),
                         **({"pageBreakAfter": True} if i == len(words) - 1 else {})})
        pct = seg.end / max(info.duration, 0.1) * 100
        if pct >= next_pct:  # print every 10% only (keeps logs/tokens small)
            print(f"  {pct:3.0f}%", flush=True)
            next_pct = (int(pct) // 10 + 1) * 10
    print(f"Дууслаа: {len(caps)} үг, {time.time() - t0:.0f}s")
    return caps


def write_caption_files(caps: list[dict], d: Path) -> None:
    save_json(d / "captions.json", caps)
    (d / "captions.srt").write_text(words_to_srt(caps), encoding="utf-8")
    (d / "transcript.txt").write_text(compact_transcript(caps), encoding="utf-8")
    low = [c for c in caps if c.get("confidence") is not None and c["confidence"] < 0.5]
    print(f"✔ {d}/captions.json | captions.srt | transcript.txt"
          + (f"  (итгэл багатай үг: {len(low)})" if low else ""))


def cmd_transcribe(a):
    src = Path(a.input)
    d = stem_dir(src)
    prompt = a.prompt or (ROOT / "config" / "whisper_prompt.txt").read_text(encoding="utf-8").strip()
    caps = transcribe(src, a.model, prompt)
    caps = apply_fixes(caps, load_fixes(ROOT / "config" / "dictionary.txt"))
    write_caption_files(caps, d)


def cmd_srt2json(a):
    """After correcting captions.srt by hand/Claude, rebuild captions.json."""
    srt = Path(a.srt)
    caps = srt_to_captions(srt.read_text(encoding="utf-8"))
    out = Path(a.output) if a.output else srt.with_name("captions.json")
    save_json(out, caps)
    (out.parent / "transcript.txt").write_text(compact_transcript(caps), encoding="utf-8")
    print(f"✔ {out} ({len(caps)} үг)")


# ---------------------------------------------------------------- clip / reframe
def layout_filter(layout: str, x: float, x2: float) -> str:
    def crop(ratio: str, cx: float) -> str:  # ratio = w/h expression
        cw = f"ih*{ratio}"
        return f"crop=w='{cw}':h=ih:x='max(0,min(iw-{cw},iw*{cx}-{cw}/2))':y=0"
    if layout == "crop":
        return f"{crop('9/16', x)},scale=1080:1920:flags=lanczos,setsar=1"
    if layout == "blur":
        return ("split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=40:4,eq=brightness=-0.1[bg];"
                "[b]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    if layout == "split":
        return (f"split[a][b];[a]{crop('9/8', x)},scale=1080:960:flags=lanczos[t];"
                f"[b]{crop('9/8', x2)},scale=1080:960:flags=lanczos[u];[t][u]vstack,setsar=1")
    if layout == "wide":
        return "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1"
    raise SystemExit(f"Unknown layout {layout}")


def make_clip(src: Path, out: Path, start: float, end: float, layout: str,
              x: float, x2: float, enhance: bool, lufs: float) -> None:
    af = ["-af", voice_chain(lufs)] if enhance else []
    ffmpeg(["-ss", f"{start:.3f}", "-i", src, "-t", f"{end - start:.3f}",
            "-filter_complex", f"[0:v]{layout_filter(layout, x, x2)}[v]", "-map", "[v]",
            "-map", "0:a?", *af, "-r", "30", *VIDEO_OUT, out])


def cmd_clip(a):
    src = Path(a.input)
    start, end = tc(a.start), tc(a.end)
    out = out_path(a.output, src, f"clip_{int(start)}")
    make_clip(src, out, start, end, a.layout, a.x, a.x2, a.enhance, a.lufs)
    print("✔", out)


# ---------------------------------------------------------------- render
def remotion_render(video: Path, caps: list[dict], out: Path, comp: str, title: str,
                    style: dict, extra: dict | None = None, assets: dict | None = None) -> None:
    job = f"job_{int(time.time())}_{video.stem}"[:60]
    pub = REMOTION / "public" / "jobs" / job
    pub.mkdir(parents=True, exist_ok=True)
    shutil.copy(video, pub / "video.mp4")
    save_json(pub / "captions.json", caps)
    extra = dict(extra or {})
    for key, path in (assets or {}).items():  # extra media (e.g. fg alpha layer)
        shutil.copy(path, pub / Path(path).name)
        extra[key] = f"jobs/{job}/{Path(path).name}"
    info = probe(video)
    props = {"video": f"jobs/{job}/video.mp4", "captions": f"jobs/{job}/captions.json",
             "title": title, "durationInSeconds": info["duration"], **style, **(extra or {})}
    props_file = pub / "props.json"
    save_json(props_file, props)
    if not (REMOTION / "node_modules").exists():
        subprocess.run([tool("npm"), "i"], cwd=REMOTION, check=True)
    try:
        subprocess.run([tool("npx"), "remotion", "render", "src/index.ts", comp, str(out.resolve()),
                        f"--props={props_file}", "--crf=18", "--log=warn"],
                       cwd=REMOTION, check=True)
    finally:
        shutil.rmtree(pub, ignore_errors=True)
    print("✔", out)


def style_from(a) -> dict:
    s = {}
    for k in ("accent", "captionY", "wordsPerPageMs", "brand"):
        v = getattr(a, k, None)
        if v is not None:
            s[k] = v
    if getattr(a, "upper", False):
        s["uppercase"] = True
    return s


def find_captions(src: Path, explicit: str | None) -> Path:
    p = Path(explicit) if explicit else stem_dir(src) / "captions.json"
    if not p.exists():
        raise SystemExit(f"Captions олдсонгүй: {p}. Эхлээд `transcribe` ажиллуул.")
    return p


def cmd_render(a):
    src = Path(a.input)
    caps = load_json(find_captions(src, a.captions))
    comp = a.comp or ("Reel" if probe(src)["height"] > probe(src)["width"] else "Wide")
    remotion_render(src, caps, out_path(a.output, src, "subs"), comp, a.title or "", style_from(a))


def cmd_reel(a):
    """Full reel: cut -> reframe 9:16 -> clean audio -> (tighten) -> captions -> Remotion render.
    Without --start/--end the whole video is used (e.g. a 1-minute phone recording)."""
    src = Path(a.input)
    dur = probe(src)["duration"]
    start = tc(a.start) if a.start else 0.0
    end = min(tc(a.end), dur) if a.end else dur
    if end - start > 90:
        print(f"⚠ Reel {end - start:.0f}s урт байна (Reels/TikTok-д 60s хүртэл хамгийн тохиромжтой).")
    d = stem_dir(src)
    tag = f"{src.stem}_reel_{int(start)}_{int(end)}"
    clip = d / f"{tag}.mp4"
    make_clip(src, clip, start, end, a.layout, a.x, a.x2, True, -14)
    if a.tight:  # remove pauses -> faster pacing (jump cuts)
        tight = d / f"{tag}_tight.mp4"
        cmd_cutsilence(argparse.Namespace(input=str(clip), output=str(tight), noise="-35dB",
                                          min=0.35, pad=0.08, dry_run=False))
        clip = tight
    full = d / "captions.json"
    if full.exists() and not a.retranscribe and not a.tight:
        print("Бүтэн транскриптээс таслав (дахин танихгүй).")
        caps = slice_captions(load_json(full), start, end)
    else:
        prompt = (ROOT / "config" / "whisper_prompt.txt").read_text(encoding="utf-8").strip()
        caps = apply_fixes(transcribe(clip, a.model, prompt), load_fixes(ROOT / "config" / "dictionary.txt"))
    cap_dir = stem_dir(clip)  # so `render <clip>` finds them automatically
    write_caption_files(caps, cap_dir)
    if a.no_render:
        print(f"Засах: {cap_dir}/captions.srt → srt2json {cap_dir}/captions.srt → render {clip}")
        return
    out = out_path(a.output, src, f"reel_{int(start)}")
    remotion_render(clip, caps, out, "Reel", a.title or "", style_from(a))


def cmd_inforeel(a):
    """16:9 podcast clip framed in a 9:16 designed reel: topic info cards + keyword pictures."""
    src = Path(a.input)
    dur = probe(src)["duration"]
    start = tc(a.start) if a.start else 0.0
    end = min(tc(a.end), dur) if a.end else dur
    d = stem_dir(src)
    tag = f"{src.stem}_info_{int(start)}_{int(end)}"
    clip = d / f"{tag}.mp4"
    make_clip(src, clip, start, end, "wide", 0.5, 0.5, True, -14)
    full = d / "captions.json"
    if full.exists() and not a.retranscribe:
        caps = slice_captions(load_json(full), start, end)
    else:
        prompt = (ROOT / "config" / "whisper_prompt.txt").read_text(encoding="utf-8").strip()
        caps = apply_fixes(transcribe(clip, a.model, prompt), load_fixes(ROOT / "config" / "dictionary.txt"))
    write_caption_files(caps, stem_dir(clip))
    extra = {"show": a.show}
    if a.cards:
        cards = load_json(Path(a.cards))
        for c in cards:  # card times are given in source-video seconds
            c["from"], c["to"] = round(c["from"] - start, 2), round(c["to"] - start, 2)
        extra["cards"] = [c for c in cards if c["to"] > 0]
    pops = [] if a.no_pops else auto_pops(caps, load_json(ROOT / "config" / "keywords.json"))
    extra["pops"] = pops
    print(f"Карт: {len(extra.get('cards', []))}, зураг: {len(pops)} "
          + ", ".join(f"{p['label']}@{p['at']}s" for p in pops))
    out = out_path(a.output, src, f"inforeel_{int(start)}")
    remotion_render(clip, caps, out, "InfoReel", a.title or "", style_from(a), extra)


def cmd_pro(a):
    """Pro reel (noorog style): face-tracked 9:16, person cut-out layer, timeline graphics."""
    from reframe import reframe
    src = Path(a.input)
    dur = probe(src)["duration"]
    start = tc(a.start) if a.start else 0.0
    end = min(tc(a.end), dur) if a.end else dur
    d = stem_dir(src)
    tag = f"{src.stem}_pro_{int(start)}_{int(end)}"
    wd = d / tag
    wd.mkdir(parents=True, exist_ok=True)
    clip = wd / "clean.mp4"
    ffmpeg(["-ss", f"{start:.3f}", "-i", src, "-t", f"{end - start:.3f}", "-af", voice_chain(-14),
            "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", clip])
    shots = Path(a.shots) if a.shots else None
    r = reframe(clip, wd, with_mask=not a.no_mask, shots_file=shots)
    full = d / "captions.json"
    if full.exists() and not a.retranscribe:
        caps = slice_captions(load_json(full), start, end)
    else:
        prompt = (ROOT / "config" / "whisper_prompt.txt").read_text(encoding="utf-8").strip()
        caps = apply_fixes(transcribe(clip, a.model, prompt), load_fixes(ROOT / "config" / "dictionary.txt"))
    write_caption_files(caps, wd)
    els = load_json(Path(a.elements)) if a.elements else []
    for e in els:  # element times are source-video seconds
        e["from"], e["to"] = round(e["from"] - start, 2), round(e["to"] - start, 2)
        if "times" in e:
            e["times"] = [round(t - start, 2) for t in e["times"]]
    extra = {"elements": [e for e in els if e["to"] > 0], "logo": a.logo}
    assets = {"fg": r["fg"]} if r["fg"] else {}
    out = out_path(a.output, src, f"pro_{int(start)}")
    remotion_render(r["base"], caps, out, "ProReel", a.title or "", style_from(a), extra, assets)


def cmd_burn(a):
    """Fast ffmpeg-only subtitle burn (no animation) – good for long episodes."""
    src = Path(a.input)
    srt = Path(a.srt) if a.srt else stem_dir(src) / "captions.srt"
    info = probe(src)
    vertical = info["height"] > info["width"]
    size, margin = (14, 110) if vertical else (20, 50)
    style = (f"FontName={a.font},FontSize={size},Bold=1,PrimaryColour=&H00FFFFFF,"
             f"OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=1,Outline=2.5,"
             f"Shadow=1,Alignment=2,MarginV={margin}")
    tmp = stem_dir(src) / "burn.srt"
    shutil.copy(srt, tmp)
    out = out_path(a.output, src, "burned")
    # run inside work dir with a relative name: Windows "C:\\" paths break filter syntax
    ffmpeg(["-i", src.resolve(), "-vf", f"subtitles=burn.srt:force_style='{style}'",
            *VIDEO_OUT, out.resolve()], cwd=tmp.parent)
    print("✔", out)


def cmd_podcast(a):
    """Full episode: clean audio -> remove silences -> transcribe -> SRT for YouTube."""
    src = Path(a.input)
    d = stem_dir(src)
    clean = d / f"{src.stem}_clean.mp4"
    cmd_enhance(argparse.Namespace(input=str(src), output=str(clean), lufs=-16, no_denoise=False))
    final = out_path(a.output, src, "episode")
    if a.no_cut:
        shutil.copy(clean, final)
    else:
        cmd_cutsilence(argparse.Namespace(input=str(clean), output=str(final), noise=a.noise,
                                          min=a.min, pad=a.pad, dry_run=False))
    if not a.no_transcribe:
        cmd_transcribe(argparse.Namespace(input=str(final), model=a.model, prompt=None))
        shutil.copy(stem_dir(final) / "captions.srt", final.with_suffix(".srt"))
        print("✔ YouTube-д оруулах субтитр:", final.with_suffix(".srt"))


# ---------------------------------------------------------------- CLI
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        s = sub.add_parser(name, help=help_)
        s.set_defaults(fn=fn)
        s.add_argument("input")
        return s

    def layout_args(s):
        s.add_argument("--layout", choices=["crop", "blur", "split", "wide"], default="crop",
                       help="crop=9:16 тайрах, blur=бүтэн кадр+бүдэг фон, split=2 хүн дээр доор, wide=16:9")
        s.add_argument("--x", type=float, default=0.5, help="Тайрах төв (0=зүүн, 1=баруун); split үед дээд хүн")
        s.add_argument("--x2", type=float, default=0.75, help="split үед доод хүний төв")

    def style_args(s):
        s.add_argument("--title", help="Эхний 3 секундэд гарах hook гарчиг")
        s.add_argument("--accent", help="Идэвхтэй үгийн өнгө, жишээ #FFD400")
        s.add_argument("--captionY", type=float, help="Субтитрийн босоо байрлал 0-1")
        s.add_argument("--wordsPerPageMs", type=int, help="Нэг дэлгэцэнд үг хэр удаан (мс)")
        s.add_argument("--brand", help="Булан дахь лого бичиг, жишээ @hashka")
        s.add_argument("--upper", action="store_true", help="ТОМ ҮСГЭЭР")

    s = add("fetch", cmd_fetch, "Google Drive / Dropbox / URL-аас input/ руу татах")
    s.add_argument("--name", help="Хадгалах нэр, жишээ ep12.mp4")

    s = sub.add_parser("setup-mn", help="Монгол Whisper turbo модель бэлдэх (нэг удаа)")
    s.set_defaults(fn=cmd_setup_mn)

    add("info", cmd_info, "Видеоны мэдээлэл")
    s = add("frame", cmd_frame, "Кадр зураг гаргах (framing шалгах)")
    s.add_argument("--at", nargs="+", default=["5"])
    s.add_argument("--width", type=int, default=480)

    s = add("enhance", cmd_enhance, "Дуу цэвэрлэх + loudness")
    s.add_argument("-o", "--output")
    s.add_argument("--lufs", type=float, default=-14)
    s.add_argument("--no-denoise", action="store_true")

    s = add("cutsilence", cmd_cutsilence, "Чимээгүй хэсгийг хасах")
    s.add_argument("-o", "--output")
    s.add_argument("--noise", default="-35dB")
    s.add_argument("--min", type=float, default=0.7, help="Хамгийн богино чимээгүй (сек)")
    s.add_argument("--pad", type=float, default=0.15, help="Үлдээх амьсгал (сек)")
    s.add_argument("--dry-run", action="store_true")

    s = add("transcribe", cmd_transcribe, "Монгол транскрипт (Whisper)")
    s.add_argument("--model", default="mn")
    s.add_argument("--prompt")

    s = sub.add_parser("srt2json", help="Засварласан SRT → captions.json")
    s.set_defaults(fn=cmd_srt2json)
    s.add_argument("srt")
    s.add_argument("-o", "--output")

    s = add("clip", cmd_clip, "Хэсэг таслах + reframe")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("-o", "--output")
    s.add_argument("--enhance", action="store_true")
    s.add_argument("--lufs", type=float, default=-14)
    layout_args(s)

    s = add("render", cmd_render, "Remotion анимацитай субтитр")
    s.add_argument("--captions")
    s.add_argument("--comp", choices=["Reel", "Wide"])
    s.add_argument("-o", "--output")
    style_args(s)

    s = add("reel", cmd_reel, "БҮТЭН REEL: таслах→9:16→дуу→субтитр→render")
    s.add_argument("--start", help="Эхлэх цаг (байхгүй бол 0)")
    s.add_argument("--end", help="Дуусах цаг (байхгүй бол видеоны төгсгөл)")
    s.add_argument("--tight", action="store_true", help="Завсар/амьсгалыг хасаж хэмнэл чангалах")
    s.add_argument("--no-render", action="store_true", help="Зөвхөн клип+субтитр бэлдэх (засварын дараа render)")
    s.add_argument("-o", "--output")
    s.add_argument("--model", default="mn")
    s.add_argument("--retranscribe", action="store_true")
    layout_args(s)
    style_args(s)

    s = add("inforeel", cmd_inforeel, "16:9 клип + инфо карт + үгэнд гарах зураг (9:16)")
    s.add_argument("--start")
    s.add_argument("--end")
    s.add_argument("--cards", help="JSON: [{from,to,icon,kicker,title,points[],stat}] (эх видеоны секунд)")
    s.add_argument("--show", default="Hashka's podcast")
    s.add_argument("--no-pops", action="store_true")
    s.add_argument("--model", default="mn")
    s.add_argument("--retranscribe", action="store_true")
    s.add_argument("-o", "--output")
    style_args(s)

    s = add("pro", cmd_pro, "PRO REEL: нүүр дагах 9:16 + хүний ард график + том үг/хэмжүүр/зураг")
    s.add_argument("--start")
    s.add_argument("--end")
    s.add_argument("--elements", help="JSON timeline (эх видеоны секунд): bigword/counter/gauge/sticker/list")
    s.add_argument("--logo", default="HASHKA'S\nPODCAST")
    s.add_argument("--shots", help="Засварласан shots.json (кадр бүрийн тайрах байрлал x)")
    s.add_argument("--no-mask", action="store_true", help="Хүний ард график хийхгүй (хурдан)")
    s.add_argument("--model", default="mn")
    s.add_argument("--retranscribe", action="store_true")
    s.add_argument("-o", "--output")
    style_args(s)

    s = add("burn", cmd_burn, "Хурдан ffmpeg субтитр шатаах")
    s.add_argument("--srt")
    s.add_argument("--font", default="Montserrat")
    s.add_argument("-o", "--output")

    s = add("podcast", cmd_podcast, "БҮТЭН ДУГААР: дуу→чимээгүй хасах→SRT")
    s.add_argument("-o", "--output")
    s.add_argument("--model", default="mn")
    s.add_argument("--noise", default="-35dB")
    s.add_argument("--min", type=float, default=1.0)
    s.add_argument("--pad", type=float, default=0.25)
    s.add_argument("--no-cut", action="store_true")
    s.add_argument("--no-transcribe", action="store_true")

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
