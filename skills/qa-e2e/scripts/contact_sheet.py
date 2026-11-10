#!/usr/bin/env python3
# Put all marked screenshots of a QA run in one image, with the file name above each shot.
# The user sees every result at a glance. The raw shots (*.raw.png) stay out.
# Usage: contact_sheet.py <evidence folder> <out.png> [columns=3] [cell width=640]
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("contact_sheet.py needs Pillow: python3 -m pip install --user Pillow")

if len(sys.argv) < 3:
    sys.exit(__doc__ or "usage: contact_sheet.py <evidence folder> <out.png> [columns] [cell width]")

folder, out = Path(sys.argv[1]), Path(sys.argv[2])
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
cell_w = int(sys.argv[4]) if len(sys.argv) > 4 else 640
label_h, pad = 28, 18

shots = sorted(p for p in folder.glob("*.png") if not p.name.endswith(".raw.png") and p.resolve() != out.resolve())
if not shots:
    sys.exit(f"no marked shots (*.png that are not *.raw.png) in {folder}")

thumbs = []
for p in shots:
    im = Image.open(p).convert("RGB")
    h = round(im.height * cell_w / im.width)
    thumbs.append((p.name, im.resize((cell_w, h), Image.LANCZOS)))

try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
except OSError:
    font = ImageFont.load_default()

rows = [thumbs[i : i + cols] for i in range(0, len(thumbs), cols)]
row_h = [label_h + max(t.height for _, t in r) + pad for r in rows]
sheet = Image.new("RGB", (cols * (cell_w + pad) + pad, sum(row_h) + pad), "white")
draw = ImageDraw.Draw(sheet)

y = pad
for r, h in zip(rows, row_h):
    for i, (name, t) in enumerate(r):
        x = pad + i * (cell_w + pad)
        draw.text((x, y), name, fill="black", font=font)
        sheet.paste(t, (x, y + label_h))
    y += h

out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out)
print(f"{out} ({len(shots)} shots)")
