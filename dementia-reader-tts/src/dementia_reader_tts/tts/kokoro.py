"""Kokoro TTS backend (82M, Apache-2.0).

Tiny and CPU-friendly - the on-device / offline path. Kokoro uses named preset
voices rather than cloning, so each VoiceConfig should set ``preset`` (e.g.
``am_michael``, ``bm_george``, ``af_heart``). ``speed`` < 1.0 slows delivery.

Install: ``uv sync --extra kokoro``.
"""

from __future__ import annotations

import numpy as np

from ..config import VoiceConfig
from .base import TTSBackend

_DEFAULT_PRESET = "af_heart"


class KokoroBackend(TTSBackend):
    sample_rate = 24000

    def __init__(self, device: str = "auto", lang_code: str = "a", **_ignored) -> None:
        from kokoro import KPipeline

        # lang_code "a" = American English, "b" = British English.
        self.pipeline = KPipeline(lang_code=lang_code)

    def synthesize(self, text: str, voice: VoiceConfig) -> np.ndarray:
        preset = voice.preset or _DEFAULT_PRESET
        chunks: list[np.ndarray] = []
        for _graphemes, _phonemes, audio in self.pipeline(
            text, voice=preset, speed=float(voice.speed or 1.0)
        ):
            arr = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
            chunks.append(arr.astype(np.float32).reshape(-1))
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks)
