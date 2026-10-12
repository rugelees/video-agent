"""Per-clip contact sheets for visual review: one image per clip, frames labelled with time.

Usage: uv run python scripts/contact_sheet.py inputs/norm -o /tmp/review [--only 20260930]
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import video_agent as va  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def sheet(src: str, out: str, cols: int = 9, cell_h: int = 266, per_sec: float = 0.2,
          min_n: int = 6, max_n: int = 45, t0: float = 0.0, t1: float | None = None,
          step_s: float | None = None):
    info = va.video_info(src)
    full = info["duration"]
    t1 = full if t1 is None else min(t1, full)
    dur = t1 - t0
    if info["width"] > info["height"]:
        cols, cell_h = 7, 190
    n = max(min_n, min(max_n, round(dur * per_sec)))
    step = dur / n
    if step_s:
        step, n = step_s, max(1, int(dur / step_s))
    cell_w = round(cell_h * info["width"] / info["height"] / 2) * 2
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", src, "-vf",
             f"fps=1/{step:.4f}:start_time={step / 2:.3f},scale={cell_w}:{cell_h}",
             "-frames:v", str(n), os.path.join(td, "f_%03d.png")], check=True)
        files = sorted(glob.glob(os.path.join(td, "f_*.png")))
        rows = math.ceil(len(files) / cols)
        im = Image.new("RGB", (cols * cell_w, rows * cell_h + 22), "black")
        d = ImageDraw.Draw(im)
        d.text((4, 4), f"{os.path.basename(src)}  {t0:.0f}-{t1:.0f}s of {full:.1f}s  {info['width']}x{info['height']}", fill="white")
        for i, f in enumerate(files):
            x, y = (i % cols) * cell_w, 22 + (i // cols) * cell_h
            im.paste(Image.open(f).convert("RGB"), (x, y))
            t = t0 + step / 2 + i * step
            d.rectangle([x, y, x + 44, y + 11], fill="black")
            d.text((x + 2, y), f"{t:.0f}s", fill="yellow")
        im.save(out, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--window", nargs=2, type=float, default=None, metavar=("T0", "T1"))
    ap.add_argument("--step", type=float, default=None, help="seconds between frames")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(a.src_dir, "*.mp4"))):
        if f.endswith(".part.mp4") or (a.only and a.only not in f):
            continue
        stem = os.path.basename(f)[:-4].replace(".f_compose_0", "").replace("dji_export_", "d")
        out = os.path.join(a.out, stem + (f"_w{int(a.window[0])}" if a.window else "") + ".jpg")
        if a.window or not os.path.exists(out):
            kw = dict(t0=a.window[0], t1=a.window[1], step_s=a.step) if a.window else {}
            sheet(f, out, **kw)
            print(out, flush=True)


if __name__ == "__main__":
    main()
