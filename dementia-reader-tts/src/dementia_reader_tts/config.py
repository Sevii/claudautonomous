"""Voice and synthesis configuration, loaded from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VoiceConfig:
    """One narrator voice.

    A voice can be defined two ways depending on the TTS backend:
      * ``reference_audio`` -> cloned by a voice-cloning backend (Chatterbox).
      * ``preset``          -> a named built-in voice (Kokoro).

    The tone knobs below are tuned low/slow on purpose: the app reads to people
    with dementia, so the brief is calm, unhurried, low-arousal warmth.
    """

    id: str
    label: str
    description: str = ""
    reference_audio: str | None = None
    preset: str | None = None

    # Chatterbox: lower exaggeration = calmer; lower cfg_weight = slower/steadier.
    exaggeration: float = 0.3
    cfg_weight: float = 0.4
    # Kokoro / time-stretch backends: <1.0 slows delivery.
    speed: float = 0.92

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceConfig":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"Unknown voice config key(s): {sorted(unknown)}")
        return cls(**data)


@dataclass
class SynthesisConfig:
    """Pipeline-wide settings."""

    backend: str = "chatterbox"
    aligner: str = "whisperx"
    language: str = "en"
    device: str = "auto"  # "auto" | "cpu" | "cuda" | "mps"

    # Pacing: silence inserted between sentences/paragraphs aids comprehension.
    sentence_pause_ms: int = 400
    paragraph_pause_ms: int = 800


def load_voices(path: str | Path) -> list[VoiceConfig]:
    """Load voices from a TOML file with ``[[voice]]`` array-of-tables."""

    path = Path(path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    raw = data.get("voice")
    if not raw:
        raise ValueError(f"No [[voice]] entries found in {path}")
    voices = [VoiceConfig.from_dict(v) for v in raw]
    ids = [v.id for v in voices]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate voice id(s) in {path}: {ids}")
    return voices
