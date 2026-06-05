"""Forced-alignment interface.

An aligner takes a rendered audio clip plus the *known* text that was spoken and
returns per-word timings (relative to the start of that clip). Because the text
is known, this is forced alignment, not transcription.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Word


class Aligner(ABC):
    @abstractmethod
    def align(self, audio_path: str, text: str, language: str = "en") -> list[Word]:
        """Return words with start/end in ms relative to the clip start."""


def get_aligner(name: str, *, device: str = "auto", language: str = "en", **kwargs) -> Aligner:
    name = name.lower()
    if name == "dummy":
        from .dummy import DummyAligner

        return DummyAligner(**kwargs)
    if name == "whisperx":
        from .whisperx_aligner import WhisperXAligner

        return WhisperXAligner(device=device, language=language, **kwargs)
    raise ValueError(f"Unknown aligner: {name!r} (try: whisperx, dummy)")
