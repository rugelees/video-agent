"""Fit a steady beat grid to a song from its kick/bass energy.

`video-agent beats` finds a tempo from every onset, which on some tracks lands on the wrong
multiple. Here the tempo is only *refined* around a known approximate BPM, the phase is chosen
where low-frequency (kick) flux peaks, and the strongest of the four beats in a bar is taken
as the downbeat.
"""
from __future__ import annotations

import numpy as np

import video_agent as va

SR, HOP, NFFT = 22050, 512, 1024


def fit_grid(path: str, bpm_guess: float, span: float = 0.05, seconds: float = 200.0):
    x = va._decode_mono(path, SR)[: int(SR * seconds)]
    frames = np.lib.stride_tricks.sliding_window_view(x, NFFT)[::HOP]
    mag = np.abs(np.fft.rfft(frames * np.hanning(NFFT), axis=1))[:, 1:10]
    env = np.concatenate([[0.0], np.maximum(0.0, np.diff(mag, axis=0)).sum(axis=1)])
    env /= env.max() or 1.0
    fps = SR / HOP
    n = len(env)
    best = (-1.0, None, None)
    for bpm in np.arange(bpm_guess * (1 - span), bpm_guess * (1 + span), bpm_guess * 0.0005):
        p = 60.0 / bpm
        for ph in np.arange(0.0, p, 0.004):
            t = np.arange(ph, n / fps - 0.1, p)
            idx = np.clip(np.round(t * fps).astype(int), 0, n - 1)
            s = (env[idx] + 0.5 * env[np.clip(idx - 1, 0, n - 1)]
                 + 0.5 * env[np.clip(idx + 1, 0, n - 1)]).mean()
            if s > best[0]:
                best = (s, p, ph)
    _, p, ph = best
    t = np.arange(ph, n / fps - 0.1, p)
    idx = np.clip(np.round(t * fps).astype(int), 0, n - 1)
    cls = [env[idx[k::4]].mean() for k in range(4)]
    down = ph + int(np.argmax(cls)) * p
    return {"period": float(p), "bpm": 60.0 / p, "phase": float(ph), "downbeat": float(down % (4 * p)),
            "bar_strength": [round(float(c), 3) for c in cls]}


if __name__ == "__main__":
    import sys
    print(fit_grid(sys.argv[1], float(sys.argv[2])))
