#!/usr/bin/env python3
# Draw a red box around each region under test, so a reviewer sees where the proof is.
# Use it on a shot that has no DOM, such as a desktop app, a chat app or a mobile screen.
# Without --crop, give each box in the pixels of the image.
# With --crop x,y,w,h, the script cuts that region first. Give each box in the pixels of the
# raw image too: the script moves the boxes into the crop, so you do not convert by hand.
# Write to a new file, and keep the original.
# Usage: mark_box.py [--crop x,y,w,h] <in.png> <out.png> <x,y,w,h> [<x,y,w,h> ...]
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("mark_box.py needs Pillow: python3 -m pip install --user Pillow")

RED = (229, 50, 45)
USAGE = "Usage: mark_box.py [--crop x,y,w,h] <in.png> <out.png> <x,y,w,h> [<x,y,w,h> ...]"


def parse(box):
    try:
        x, y, w, h = (int(float(v)) for v in box.split(","))
    except ValueError:
        sys.exit(f"Bad box {box!r}: give x,y,w,h in pixels")
    return x, y, w, h


args = sys.argv[1:]
crop = None
if args[:1] == ["--crop"]:
    if len(args) < 2:
        sys.exit(USAGE)
    crop = parse(args[1])
    args = args[2:]
if len(args) < 3:
    sys.exit(USAGE)
src, dst, boxes = args[0], args[1], args[2:]
if src == dst:
    sys.exit("Write the box to a new file. The original stays as the raw proof.")

img = Image.open(src).convert("RGB")
ox, oy = 0, 0
if crop:
    cx, cy, cw, ch = crop
    if cw <= 0 or ch <= 0 or cx < 0 or cy < 0 or cx + cw > img.width or cy + ch > img.height:
        sys.exit(f"Crop {crop} is outside the image {img.width}x{img.height}")
    img = img.crop((cx, cy, cx + cw, cy + ch))
    ox, oy = cx, cy
# A 3 px line is too thin to see on a 2x Retina shot, so the line grows with the image.
line = max(3, round(max(img.size) / 400))
draw = ImageDraw.Draw(img)
for box in boxes:
    x, y, w, h = parse(box)
    x, y = x - ox, y - oy
    if w <= 0 or h <= 0 or x + w > img.width or y + h > img.height or x < 0 or y < 0:
        where = "the crop" if crop else "the image"
        sys.exit(f"Box {box} is outside {where} {img.width}x{img.height}")
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=RED, width=line)
img.save(dst)
print(f"ok {dst} ({len(boxes)} box, line {line} px{', crop ' + ','.join(map(str, crop)) if crop else ''})")
