"""Offline stub backend: deterministic tone, no models, no network.

Used for tests and for verifying the whole pipeline (segmentation -> concat ->
alignment -> packaging) without a GPU or model downloads. Duration scales with
word count so the resulting sync maps look realistic.
"""

from __future__ import annotations

import numpy as np

from ..config import VoiceConfig
from .base import TTSBackend

_SECONDS_PER_WORD = 0.38
_LEAD_SECONDS = 0.15


class DummyBackend(TTSBackend):
    def __init__(self, sample_rate: int = 24000, **_ignored) -> None:
        self.sample_rate = sample_rate

    def synthesize(self, text: str, voice: VoiceConfig) -> np.ndarray:
        n_words = max(1, len(text.split()))
        seconds = _LEAD_SECONDS + n_words * _SECONDS_PER_WORD * float(voice.speed or 1.0)
        n = int(self.sample_rate * seconds)
        t = np.arange(n, dtype=np.float32) / self.sample_rate
        # A quiet, distinct pitch per voice so output is audibly different.
        freq = {"baritone": 110.0, "tenor": 165.0, "alto": 220.0}.get(voice.id, 180.0)
        envelope = np.minimum(1.0, np.minimum(t * 8, (seconds - t) * 8)).astype(np.float32)
        return (0.05 * envelope * np.sin(2 * np.pi * freq * t)).astype(np.float32)
