"""Pre-render narrated audiobooks with open-weights TTS + forced-alignment word maps.

Pipeline: text -> sentences -> [TTS backend] -> chapter audio
                                            -> [forced aligner] -> word sync map
                                            -> packaged per book x voice.
"""

from .models import ChapterAudio, Sentence, Word
from .config import VoiceConfig, SynthesisConfig

__all__ = [
    "ChapterAudio",
    "Sentence",
    "Word",
    "VoiceConfig",
    "SynthesisConfig",
]

__version__ = "0.1.0"
