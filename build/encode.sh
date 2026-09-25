#!/bin/zsh
# Rebuilds bg.mp4 (seamless loop: the Kling clip forward, then reversed) and bg.jpg (its first frame).
# Usage: zsh build/encode.sh [source-clip.mp4]
set -e
SRC="${1:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/AI/Media Gen/2026-09-25-magnifica-bg-majestic-cross-a/kling/video-01.mp4}"
ROOT="${0:A:h}/.."
PINGPONG='[0:v]split[f][r];[r]reverse[rv];[f][rv]concat=n=2:v=1:a=0'
# HEVC for Apple devices (hardware decode on every iPhone): 1.39 MB at VMAF 93.3 vs the H.264 fallback's
# 2.01 MB at VMAF 91.0, both scored against a near-lossless reference (see README).
ffmpeg -nostdin -loglevel error -y -i "$SRC" -filter_complex "$PINGPONG,scale=1080:-2,fps=24" \
  -an -c:v libx265 -crf 28 -preset slow -tag:v hvc1 -x265-params log-level=error -pix_fmt yuv420p -movflags +faststart "$ROOT/bg-hevc.mp4"
# H.264 fallback for browsers without HEVC (Firefox, older Android)
ffmpeg -nostdin -loglevel error -y -i "$SRC" -filter_complex "$PINGPONG,scale=1080:-2,fps=24" \
  -an -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -movflags +faststart "$ROOT/bg.mp4"
ffmpeg -nostdin -loglevel error -y -i "$SRC" -vf "select=eq(n\,0),scale=720:-2" -frames:v 1 -q:v 4 "$ROOT/bg.jpg"
for f in bg-hevc.mp4 bg.mp4 bg.jpg; do
  printf '%-7s %6.2f MB  ' "$f" "$(( $(stat -f%z "$ROOT/$f") / 1e6 ))"
  ffprobe -v error -show_entries stream=width,height:format=duration -of csv=p=0 "$ROOT/$f" | tr '\n' ' '; echo
done
