"""Mono float32 audio helpers (numpy + soundfile)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def silence(duration_ms: int, sample_rate: int) -> np.ndarray:
    n = int(round(sample_rate * duration_ms / 1000.0))
    return np.zeros(max(0, n), dtype=np.float32)


def concat(segments: list[np.ndarray]) -> np.ndarray:
    if not segments:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate([np.asarray(s, dtype=np.float32).reshape(-1) for s in segments])


def duration_ms(audio: np.ndarray, sample_rate: int) -> int:
    return int(round(len(audio) / sample_rate * 1000.0))


def save_wav(path: str | Path, audio: np.ndarray, sample_rate: int) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(np.asarray(audio, dtype=np.float32).reshape(-1), -1.0, 1.0)
    sf.write(str(path), audio, sample_rate, subtype="PCM_16")


def read_duration_ms(path: str | Path) -> int:
    info = sf.info(str(path))
    return int(round(info.frames / info.samplerate * 1000.0))
