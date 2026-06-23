#!/usr/bin/env python3
"""Render a recorded `dispatch` demo session into the committed README GIF + LinkedIn MP4.

The recording is editorial — you watch the raw session and pick which time ranges to keep.
This script makes the *post-processing* reproducible so the demo can be regenerated whenever
`dispatch` changes: keep-ranges -> speed-up -> (GIF: final-frame hold + downscale) -> optimize.

Pipeline (tuned against README-GIF best practices — see ../../private/DEMO-RECORDING.md):
  trim+concat the keep-ranges  ->  setpts speed-up
    -> MP4 : full-resolution, the LinkedIn asset
    -> GIF : + final-frame hold, scale to --width (lanczos),
             palettegen stats_mode=diff, paletteuse dither=none  (crisp terminal text),
             gifsicle -O3 --lossy=30  (small file)

Requires `ffmpeg` and `gifsicle` on PATH (pure Python 3 stdlib otherwise).

Example (reproduces the shipped demo):
  python3 tools/demos/render.py /tmp/dispatch-demo/dispatch-session-full.mp4 \\
      --keep 0:00-0:51 1:07-1:10 1:15-1:35 1:56-2:17 --speed 1.5
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def to_seconds(stamp: str) -> float:
    """'1:56' / '116' / '1:56.5' -> seconds."""
    sec = 0.0
    for part in stamp.split(":"):
        sec = sec * 60 + float(part)
    return sec


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", help="the recorded full-session MP4 (from the VHS tape)")
    ap.add_argument("--keep", nargs="+", required=True, metavar="START-END",
                    help="time ranges to keep, e.g. 0:00-0:51 1:56-2:17 (mm:ss or seconds)")
    ap.add_argument("--speed", type=float, default=1.5, help="playback speed-up (default 1.5)")
    ap.add_argument("--width", type=int, default=900, help="GIF width px (default 900 = GitHub column)")
    ap.add_argument("--fps", type=int, default=15, help="GIF fps (default 15)")
    ap.add_argument("--hold", type=float, default=2.5, help="seconds to hold the final frame before looping")
    ap.add_argument("--lossy", type=int, default=30, help="gifsicle --lossy level (default 30)")
    ap.add_argument("--out-gif", default="assets/dispatch-demo.gif")
    ap.add_argument("--out-mp4", default="assets/dispatch-demo.mp4")
    args = ap.parse_args()

    for tool in ("ffmpeg", "gifsicle"):
        if shutil.which(tool) is None:
            sys.exit(f"error: '{tool}' not found on PATH (brew install ffmpeg gifsicle)")
    if not os.path.isfile(args.session):
        sys.exit(f"error: session not found: {args.session}")

    # keep-ranges -> trim+concat -> speed
    segs, labels = [], []
    for i, rng in enumerate(args.keep):
        start, end = rng.split("-")
        segs.append(f"[0:v]trim={to_seconds(start)}:{to_seconds(end)},setpts=PTS-STARTPTS[k{i}]")
        labels.append(f"[k{i}]")
    cut_filter = ";".join(segs + [
        "".join(labels) + f"concat=n={len(labels)}:v=1[cat]",
        f"[cat]setpts=PTS/{args.speed}[v]",
    ])

    tmp = tempfile.mkdtemp(prefix="dispatch-demo-")
    try:
        cut = os.path.join(tmp, "cut.mp4")
        run(["ffmpeg", "-y", "-i", args.session, "-filter_complex", cut_filter,
             "-map", "[v]", "-an", "-pix_fmt", "yuv420p", cut])

        # MP4 asset = the sped cut, full resolution
        os.makedirs(os.path.dirname(args.out_mp4) or ".", exist_ok=True)
        shutil.copyfile(cut, args.out_mp4)

        # GIF: final-frame hold -> downscale -> palette (no dither) -> gifsicle
        freeze = os.path.join(tmp, "freeze.mp4")
        run(["ffmpeg", "-y", "-i", cut, "-vf",
             f"tpad=stop_mode=clone:stop_duration={args.hold}", "-an", freeze])
        scale = f"fps={args.fps},scale={args.width}:-1:flags=lanczos"
        palette = os.path.join(tmp, "palette.png")
        run(["ffmpeg", "-y", "-i", freeze, "-vf",
             f"{scale},palettegen=max_colors=256:stats_mode=diff", palette])
        raw_gif = os.path.join(tmp, "raw.gif")
        run(["ffmpeg", "-y", "-i", freeze, "-i", palette, "-lavfi",
             f"{scale}[x];[x][1:v]paletteuse=dither=none", raw_gif])
        os.makedirs(os.path.dirname(args.out_gif) or ".", exist_ok=True)
        run(["gifsicle", "-O3", f"--lossy={args.lossy}", raw_gif, "-o", args.out_gif])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    mb = os.path.getsize(args.out_gif) / 1e6
    print(f"GIF -> {args.out_gif}  ({mb:.1f} MB)")
    print(f"MP4 -> {args.out_mp4}")
    if mb > 5:
        print("note: GIF > 5 MB — drop --fps to 12, then --lossy to 60, then --width to 800.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
