"""TTS backend interface.

A backend turns one sentence of text into a mono float32 numpy waveform at
``self.sample_rate``. Backends are constructed via :func:`get_backend` so the
heavy ML dependencies are imported lazily, only when actually selected.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..config import VoiceConfig


class TTSBackend(ABC):
    sample_rate: int

    @abstractmethod
    def synthesize(self, text: str, voice: VoiceConfig) -> np.ndarray:
        """Render ``text`` in ``voice`` -> mono float32 at ``self.sample_rate``."""

    def warmup(self) -> None:  # optional pre-flight (model load, etc.)
        return None


def get_backend(name: str, *, device: str = "auto", **kwargs) -> TTSBackend:
    name = name.lower()
    if name == "dummy":
        from .dummy import DummyBackend

        return DummyBackend(**kwargs)
    if name == "chatterbox":
        from .chatterbox import ChatterboxBackend

        return ChatterboxBackend(device=device, **kwargs)
    if name == "kokoro":
        from .kokoro import KokoroBackend

        return KokoroBackend(device=device, **kwargs)
    raise ValueError(f"Unknown TTS backend: {name!r} (try: chatterbox, kokoro, dummy)")
