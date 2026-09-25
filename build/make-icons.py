"""Crops the Home Screen icons (512 and 180 px) around the cross in the source still.

Run: python3 build/make-icons.py [source-still.png]
"""
import sys
from pathlib import Path

from PIL import Image

DEFAULT_SRC = (Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/AI/Media Gen"
               / "2026-09-25-magnifica-bg-majestic-cross-a/image-01.png")
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
ROOT = Path(__file__).resolve().parent.parent

# The cross is centred horizontally and sits in the upper part of the still; this square holds all of it.
CENTER_Y, SIDE_OF_WIDTH = 0.34, 0.92

im = Image.open(SRC).convert("RGB")
w, h = im.size
side = int(w * SIDE_OF_WIDTH)
cx, cy = w // 2, int(h * CENTER_Y)
box = (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)
square = im.crop(box)
# 256-colour dithered PNG: 481 KB -> ~166 KB with no visible change (it is precached for offline use)
square.resize((512, 512), Image.LANCZOS).quantize(
    colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG
).save(ROOT / "icon-512.png", optimize=True)
square.resize((180, 180), Image.LANCZOS).save(ROOT / "apple-touch-icon.png", optimize=True)
print("icons cropped from", box, "of", im.size)
