"""Serializable data models for the sync map (audio + word timings)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Word:
    """One spoken word and where it lands in the chapter audio (milliseconds)."""

    word: str
    start_ms: int
    end_ms: int
    score: float | None = None


@dataclass
class Sentence:
    """A sentence: its text, span in the chapter, and per-word timings."""

    index: int
    text: str
    start_ms: int
    end_ms: int
    words: list[Word] = field(default_factory=list)


@dataclass
class ChapterAudio:
    """Everything an app needs to play a chapter and highlight words as they're read."""

    book: str
    chapter: str
    voice: str
    audio_file: str
    sample_rate: int
    duration_ms: int
    sentences: list[Sentence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
