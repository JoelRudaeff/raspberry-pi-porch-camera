#!/usr/bin/env python3
"""Synthesise three short bird-of-prey style calls used to scare pigeons off the balcony.

Writes scare_1.wav .. scare_3.wav (mono, 16-bit, 44.1 kHz) into the directory given as argv[1].
Three variants are played at random so the pigeons get used to them more slowly.
"""
import math
import random
import struct
import sys
import wave
from pathlib import Path

RATE = 44100
rng = random.Random(7)


def screech(dur, f_start, f_end, rough=0.4):
    """Descending, raspy 'kee-eeer' call, like a hawk's scream."""
    n = int(dur * RATE)
    out, phase, noise = [], 0.0, 0.0
    for i in range(n):
        t = i / RATE
        x = t / dur
        f = f_start * (f_end / f_start) ** x * (1 + 0.012 * math.sin(2 * math.pi * 28 * t))
        phase += 2 * math.pi * f / RATE
        tone = math.sin(phase) + 0.45 * math.sin(2 * phase) + 0.25 * math.sin(3 * phase)
        noise = 0.92 * noise + 0.08 * rng.uniform(-1, 1)          # low-passed noise for rasp
        am = 1 - rough * (0.5 + 0.5 * math.sin(2 * math.pi * 90 * t)) + 1.5 * noise
        env = min(1.0, t / 0.04) * (math.exp(-(t - (dur - 0.25)) / 0.08) if t > dur - 0.25 else 1.0)
        out.append(tone * am * env)
    return out


def kek(count, freq=2600, length=0.11, gap=0.09):
    """Short repeated 'kek-kek-kek' alarm notes, like a falcon."""
    out = []
    for _ in range(count):
        n = int(length * RATE)
        for i in range(n):
            t = i / RATE
            env = math.sin(math.pi * t / length) ** 2
            p = 2 * math.pi * freq * (1 - 0.15 * t / length) * t
            out.append((math.sin(p) + 0.5 * math.sin(2 * p)) * env)
        out += silence(gap)
    return out


def silence(dur):
    return [0.0] * int(dur * RATE)


def write(path, samples):
    peak = max(abs(s) for s in samples) or 1.0
    frames = b"".join(struct.pack("<h", int(32767 * 0.8 * s / peak)) for s in samples)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    variants = {
        "scare_1.wav": screech(0.9, 3000, 1900) + silence(0.35) + screech(0.9, 3000, 1850),
        "scare_2.wav": screech(0.6, 3400, 2200) + silence(0.25) + screech(0.6, 3300, 2150)
        + silence(0.25) + screech(0.6, 3400, 2100),
        "scare_3.wav": screech(1.3, 2800, 1700, rough=0.5) + silence(0.3) + kek(4),
    }
    for name, samples in variants.items():
        write(out / name, samples + silence(0.2))
        print(f"{name}: {len(samples) / RATE:.1f} s")


if __name__ == "__main__":
    main()
