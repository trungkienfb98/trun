"""Vietnamese speech-to-text with word timestamps (offline, sherpa-onnx zipformer-vi).

Usage: python3 transcribe.py <video> <words.json>

Writes [{"word": "TẠI", "start": 0.0, "end": 0.6}, ...]. Text comes out UPPERCASE without
punctuation; fix spelling/case/brand names when writing the plan.
The model (~260 MB) is downloaded once from GitHub Releases into ~/.cache/edit-video-bds.
"""
import json
import os
import subprocess
import sys
import tarfile
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_exe  # noqa: E402

MODEL = "sherpa-onnx-zipformer-vi-2025-04-20"
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL}.tar.bz2"
CACHE = os.path.expanduser("~/.cache/edit-video-bds")


def ensure_model():
    d = os.path.join(CACHE, MODEL)
    if os.path.isdir(d):
        return d
    os.makedirs(CACHE, exist_ok=True)
    tmp = os.path.join(CACHE, MODEL + ".tar.bz2")
    print("Downloading speech model (~260 MB)...", file=sys.stderr)
    urllib.request.urlretrieve(URL, tmp)
    with tarfile.open(tmp) as t:
        t.extractall(CACHE)
    os.remove(tmp)
    return d


def load_audio(path):
    pcm = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768


def main(src, out):
    try:
        import sherpa_onnx as so
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sherpa-onnx"], check=True)
        import sherpa_onnx as so
    d = ensure_model()
    rec = so.OfflineRecognizer.from_transducer(
        encoder=f"{d}/encoder-epoch-12-avg-8.onnx", decoder=f"{d}/decoder-epoch-12-avg-8.onnx",
        joiner=f"{d}/joiner-epoch-12-avg-8.onnx", tokens=f"{d}/tokens.txt", num_threads=4)
    audio = load_audio(src)
    words = []
    # decode in ~25 s windows so long videos stay within model limits
    win = 16000 * 25
    for off in range(0, len(audio), win):
        s = rec.create_stream()
        s.accept_waveform(16000, audio[off:off + win])
        rec.decode_stream(s)
        base = off / 16000
        for tok, ts in zip(s.result.tokens, s.result.timestamps):
            if tok.startswith((" ", "▁")) or not words or words[-1].get("_win") != off:
                words.append({"word": tok.strip(" ▁"), "start": round(base + ts, 2), "_win": off})
            else:
                words[-1]["word"] += tok
    total = len(audio) / 16000
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else total
        w["end"] = round(min(nxt, w["start"] + 0.8), 2)
        w.pop("_win")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=1)
    print(" ".join(w["word"] for w in words))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
