"""Chatterbox TTS backend (Resemble AI, MIT weights).

High-quality voice cloning. Each voice clones a short reference recording
(``voice.reference_audio``). For the calm, low-arousal brief we run with low
``exaggeration`` and low ``cfg_weight`` (steadier, more deliberate pacing).

Install: ``uv sync --extra chatterbox`` (pulls torch + torchaudio).
"""

from __future__ import annotations

import numpy as np

from ..config import VoiceConfig
from ..devices import resolve_device
from .base import TTSBackend


class ChatterboxBackend(TTSBackend):
    def __init__(self, device: str = "auto", **_ignored) -> None:
        from chatterbox.tts import ChatterboxTTS

        self.device = resolve_device(device)
        self.model = ChatterboxTTS.from_pretrained(device=self.device)
        # Chatterbox renders at the model's native sample rate.
        self.sample_rate = int(self.model.sr)

    def synthesize(self, text: str, voice: VoiceConfig) -> np.ndarray:
        kwargs: dict = {
            "exaggeration": float(voice.exaggeration),
            "cfg_weight": float(voice.cfg_weight),
        }
        if voice.reference_audio:
            kwargs["audio_prompt_path"] = voice.reference_audio
        wav = self.model.generate(text, **kwargs)
        # wav: torch.Tensor [1, n] -> mono float32 numpy
        return wav.squeeze(0).detach().cpu().numpy().astype(np.float32)
