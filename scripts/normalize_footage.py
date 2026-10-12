"""Normalize mixed-source footage into one edit-friendly format.

Every video in --src becomes a 1080p, constant-24fps, SDR (Rec.709), AAC-audio MP4 in --out,
with the displayed orientation baked in (portrait -> 1080x1920, landscape -> 1920x1080):

- rotation tags are applied (ffmpeg autorotate) and the target size follows the *displayed* shape
- HLG HDR (iPhone) is tone-mapped to SDR so it matches the already-graded action-cam clips
- 25 / 24.9 fps sources are conformed to 24 by a ~4% slowdown (no dropped frames, no hitch);
  other rates (30/60) are blended down with the `framerate` filter
- --vcrop SUBSTR=FOCUS re-crops matching landscape clips to a true 9:16 (from full-res source)
- resumable: finished outputs are skipped

Usage: uv run python scripts/normalize_footage.py inputs/cartagena -o inputs/norm [-j 2]
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import video_agent as va  # noqa: E402

VIDEO_EXTS = (".mov", ".mp4", ".m4v")
TONEMAP_HLG = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
               "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")
OUT_FPS = 24


def _color_transfer(path: str) -> str:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=color_transfer", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return out


def _has_audio(path: str) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout
    return "audio" in out


def build_cmd(src: str, dst: str, threads: int, crf: int, preset: str,
              vcrop: float | None = None) -> list[str]:
    info = va.video_info(src)
    w, h = (1080, 1920) if info["height"] > info["width"] else (1920, 1080)
    fps = info["fps"]
    vf = []
    if vcrop is not None:
        w, h = 1080, 1920
        vf.append(f"crop=trunc(ih*9/16/2)*2:ih:trunc((iw-trunc(ih*9/16/2)*2)*{vcrop}/2)*2:0")
    vf.append(f"scale={w}:{h}:flags=lanczos")
    if _color_transfer(src) in ("arib-std-b67", "smpte2084"):
        vf.append(TONEMAP_HLG)
    af = ["aresample=48000"]
    if abs(fps - OUT_FPS) < 0.05:
        pass
    elif abs(fps - 25) < 0.2:
        vf.append(f"setpts=PTS*{fps / OUT_FPS:.6f}")
        af.append(f"atempo={OUT_FPS / fps:.6f}")
    else:
        vf.append(f"framerate=fps={OUT_FPS}")
    vf.append(f"fps={OUT_FPS}")
    vf.append("format=yuv420p")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-threads", str(threads),
           "-i", src, "-map", "0:v:0", "-vf", ",".join(vf)]
    if _has_audio(src):
        cmd += ["-map", "0:a:0", "-af", ",".join(af), "-c:a", "aac", "-b:a", "192k", "-ac", "2"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-g", "48",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-color_range", "tv", "-movflags", "+faststart", dst]
    return cmd


def run_one(args):
    src, out_dir, threads, crf, preset, vcrop = args
    stem = os.path.splitext(os.path.basename(src))[0] + ("_v" if vcrop is not None else "")
    dst = os.path.join(out_dir, stem + ".mp4")
    if os.path.exists(dst):
        return f"skip  {stem}"
    tmp = dst + ".part.mp4"
    p = subprocess.run(build_cmd(src, tmp, threads, crf, preset, vcrop), capture_output=True, text=True)
    if p.returncode != 0:
        return f"FAIL  {stem}: {p.stderr.strip()[-300:]}"
    os.replace(tmp, dst)
    return f"done  {stem}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-j", "--jobs", type=int, default=2)
    ap.add_argument("--threads", type=int, default=2, help="ffmpeg threads per job")
    ap.add_argument("--crf", type=int, default=14)
    ap.add_argument("--preset", default="fast")
    ap.add_argument("--only", default=None, help="substring filter on file name")
    ap.add_argument("--vcrop", action="append", default=[], metavar="SUBSTR=FOCUS",
                    help="also write a 9:16 center-cropped '<name>_v.mp4' of matching landscape "
                         "files; FOCUS 0..1 slides the crop window left->right (repeatable)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files = sorted(f for f in glob.glob(os.path.join(a.src, "*"))
                   if f.lower().endswith(VIDEO_EXTS) and (not a.only or a.only in f))
    jobs = [(f, a.out, a.threads, a.crf, a.preset, None) for f in files]
    for spec in a.vcrop:
        key, _, focus = spec.partition("=")
        jobs += [(f, a.out, a.threads, a.crf, a.preset, float(focus or 0.5))
                 for f in files if key in f]
    with ThreadPoolExecutor(a.jobs) as ex:
        for i, msg in enumerate(ex.map(run_one, jobs), 1):
            print(f"[{i}/{len(jobs)}] {msg}", flush=True)


if __name__ == "__main__":
    main()
