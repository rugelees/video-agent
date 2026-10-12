"""Turn still photos (JPG/HEIC) into silent 24fps clips so they can sit in an EDL.

Each photo is auto-oriented from EXIF, capped to --max-side, and held for --seconds. Use the
EDL's `punch` for a slow push and `fit: blur` for photos whose shape differs from the canvas.

Usage: uv run --with pillow-heif python scripts/photo_clips.py photo1.HEIC photo2.JPG -o inputs/norm
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile

from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--max-side", type=int, default=2160)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for p in a.photos:
        stem = "photo_" + os.path.splitext(os.path.basename(p))[0]
        dst = os.path.join(a.out, stem + ".mp4")
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        im.thumbnail((a.max_side, a.max_side), Image.LANCZOS)
        w, h = im.size
        im = im.crop((0, 0, w - w % 2, h - h % 2))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t:
            im.save(t.name)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(a.fps),
             "-i", t.name, "-t", f"{a.seconds}", "-c:v", "libx264", "-crf", "12",
             "-preset", "medium", "-pix_fmt", "yuv420p", "-color_range", "tv",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-movflags", "+faststart", dst], check=True)
        os.unlink(t.name)
        print(dst, im.size)


if __name__ == "__main__":
    main()
