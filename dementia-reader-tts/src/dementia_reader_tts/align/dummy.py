"""Offline stub aligner: distributes words evenly across the clip duration.

No ML, no ffmpeg. Lets the full pipeline run anywhere and produces a plausibly
shaped sync map for tests and front-end development.
"""

from __future__ import annotations

from ..audio import read_duration_ms
from ..models import Word


class DummyAligner:
    def align(self, audio_path: str, text: str, language: str = "en") -> list[Word]:
        words = text.split()
        if not words:
            return []
        total = read_duration_ms(audio_path)
        # Reserve a little lead-in so word 0 doesn't start at 0ms (matches TTS).
        lead = min(150, total // 10)
        span = max(0, total - lead)
        per = span / len(words)
        out: list[Word] = []
        for i, w in enumerate(words):
            start = int(lead + i * per)
            end = int(lead + (i + 1) * per)
            out.append(Word(word=w, start_ms=start, end_ms=end, score=None))
        return out
