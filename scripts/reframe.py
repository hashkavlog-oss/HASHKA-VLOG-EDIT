"""Smart 16:9 -> 9:16 reframe + person mask (for 'graphics behind the speaker').

One OpenCV pass over the clip:
  1. detect shot cuts (histogram difference)
  2. detect faces (MediaPipe) -> one stable crop position per shot
  3. crop + scale to 1080x1920 -> base.mp4
  4. person segmentation (MediaPipe selfie multiclass) -> fg.webm (VP9 with alpha)
Per-shot crop positions are saved to shots.json; edit "x" there and rerun with
--shots to override (e.g. choose the other person in a wide shot).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from common import ROOT, save_json

MODELS = ROOT / "models"
W, H = 1080, 1920


def _face_detector():
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    return vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "face_detector.tflite")),
        min_detection_confidence=0.5)), mp


def _segmenter():
    from mediapipe.tasks.python import BaseOptions, vision
    return vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "selfie_multiclass.tflite")),
        output_category_mask=False, output_confidence_masks=True))


def analyse(src: Path, step: int = 3) -> tuple[list[dict], float, int]:
    """Return shots [{start,end,x}] where x = crop centre 0..1."""
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    det, mp = _face_detector()
    cuts, faces, prev_hist, i = [0], {}, None, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (160, 90))
        hist = cv2.calcHist([cv2.cvtColor(small, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        if prev_hist is not None and cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA) > 0.35 \
                and i - cuts[-1] > fps * 0.5:
            cuts.append(i)
        prev_hist = hist
        if i % step == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
            fw = frame.shape[1]
            faces[i] = [((d.bounding_box.origin_x + d.bounding_box.width / 2) / fw,
                         d.bounding_box.width * d.bounding_box.height) for d in res.detections]
        i += 1
    cap.release()
    n = i
    cuts.append(n)
    shots = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        found = [f for k, fs in faces.items() if a <= k < b for f in fs]
        if found:
            # biggest face wins; weight by area so the main subject dominates
            big = max(found, key=lambda f: f[1])[1]
            xs = [f[0] for f in found if f[1] > big * 0.45]
            x = float(np.median(xs))
        else:
            x = 0.5
        nfaces = max((len(fs) for k, fs in faces.items() if a <= k < b), default=0)
        shots.append({"start": round(a / fps, 3), "end": round(b / fps, 3), "x": round(x, 3),
                      "faces": nfaces})
    return shots, fps, n


def render(src: Path, shots: list[dict], out_base: Path, out_fg: Path | None, fps: float) -> None:
    cap = cv2.VideoCapture(str(src))
    sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p"]
    base = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", str(src),
                             "-map", "0:v", "-map", "1:a?", *enc, "-c:a", "aac", "-b:a", "192k",
                             "-shortest", str(out_base)], stdin=subprocess.PIPE)
    fg = seg = None
    if out_fg:
        fg = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                               "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libvpx-vp9",
                               "-pix_fmt", "yuva420p", "-b:v", "4M", "-deadline", "realtime",
                               "-cpu-used", "8", "-auto-alt-ref", "0", str(out_fg)], stdin=subprocess.PIPE)
        seg = _segmenter()
        import mediapipe as mp
    prev_mask, i, si = None, 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        while si < len(shots) - 1 and t >= shots[si]["end"]:
            si += 1
            prev_mask = None  # no mask smoothing across cuts
        sh_ = shots[si]
        zoom = max(1.0, float(sh_.get("zoom", 1.0)))  # >1 = punch in (wide shots)
        ch = int(sh / zoom) // 2 * 2
        cw = int(round(ch * 9 / 16)) // 2 * 2
        x0 = max(0, min(sw - cw, int(round(sh_["x"] * sw - cw / 2))))
        y0 = max(0, min(sh - ch, int(round(sh_.get("y", 0.5) * sh - ch / 2))))
        region = frame[y0:y0 + ch, x0:x0 + cw]
        crop = cv2.resize(region, (W, H), interpolation=cv2.INTER_LANCZOS4)
        base.stdin.write(crop.tobytes())
        if fg:
            small = cv2.cvtColor(cv2.resize(region, (288, 512)), cv2.COLOR_BGR2RGB)
            res = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=small))
            person = 1.0 - res.confidence_masks[0].numpy_view()  # 0 = background class
            if prev_mask is not None:
                person = 0.6 * person + 0.4 * prev_mask
            prev_mask = person
            m = cv2.resize(person, (W, H), interpolation=cv2.INTER_LINEAR)
            m = cv2.GaussianBlur(m, (0, 0), 3)
            m = np.clip((m - 0.35) / 0.35, 0, 1)
            bgra = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
            bgra[:, :, 3] = (m * 255).astype(np.uint8)
            fg.stdin.write(bgra.tobytes())
        i += 1
    cap.release()
    for p in (base, fg):
        if p:
            p.stdin.close()
            p.wait()


def reframe(src: Path, work: Path, with_mask: bool = True, shots_file: Path | None = None) -> dict:
    if shots_file and shots_file.exists():
        shots = json.loads(shots_file.read_text())
        fps = cv2.VideoCapture(str(src)).get(cv2.CAP_PROP_FPS) or 30
    else:
        shots, fps, _ = analyse(src)
    save_json(work / "shots.json", shots)
    print(f"Кадр: {len(shots)} ширхэг → " + ", ".join(f"{s['start']:.0f}s:x{s['x']:.2f}" for s in shots[:12]))
    base, fg = work / "base.mp4", (work / "fg.webm" if with_mask else None)
    render(src, shots, base, fg, fps)
    return {"base": base, "fg": fg, "shots": shots}
