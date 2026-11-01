#!/usr/bin/env python3
# Draw a red box around each region under test, so a reviewer sees where the proof is.
# Use it on a shot that has no DOM, such as a desktop app, a chat app or a mobile screen.
# Give the box in the pixels of the image, after the crop. Write to a new file, and keep the original.
# Usage: mark_box.py <in.png> <out.png> <x,y,w,h> [<x,y,w,h> ...]
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("mark_box.py needs Pillow: python3 -m pip install --user Pillow")

RED = (229, 50, 45)

if len(sys.argv) < 4:
    sys.exit("Usage: mark_box.py <in.png> <out.png> <x,y,w,h> [<x,y,w,h> ...]")
src, dst, boxes = sys.argv[1], sys.argv[2], sys.argv[3:]
if src == dst:
    sys.exit("Write the box to a new file. The original stays as the raw proof.")

img = Image.open(src).convert("RGB")
# A 3 px line is too thin to see on a 2x Retina shot, so the line grows with the image.
line = max(3, round(max(img.size) / 400))
draw = ImageDraw.Draw(img)
for box in boxes:
    try:
        x, y, w, h = (int(float(v)) for v in box.split(","))
    except ValueError:
        sys.exit(f"Bad box {box!r}: give x,y,w,h in pixels")
    if w <= 0 or h <= 0 or x + w > img.width or y + h > img.height or x < 0 or y < 0:
        sys.exit(f"Box {box} is outside the image {img.width}x{img.height}")
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=RED, width=line)
img.save(dst)
print(f"ok {dst} ({len(boxes)} box, line {line} px)")
