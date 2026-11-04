#!/usr/bin/env bash
# Small MediaPipe models for face tracking + person cut-out (pro reels).
set -e
cd "$(dirname "$0")/.." && mkdir -p models
B=https://storage.googleapis.com/mediapipe-models
[ -f models/face_detector.tflite ] || curl -sSfL -o models/face_detector.tflite $B/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
[ -f models/selfie_multiclass.tflite ] || curl -sSfL -o models/selfie_multiclass.tflite $B/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
echo "✔ models/"
