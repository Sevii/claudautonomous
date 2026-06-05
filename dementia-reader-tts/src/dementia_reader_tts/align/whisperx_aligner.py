"""WhisperX forced-alignment backend -> word-level timestamps.

Reuses the wav2vec2 alignment models WhisperX ships with. We feed the known
sentence text as a single segment spanning the whole clip, so WhisperX aligns
(rather than transcribes) and returns accurate word boundaries.

Install: ``uv sync --extra align``. Requires ffmpeg on PATH (WhisperX loads
audio via ffmpeg).
"""

from __future__ import annotations

from ..devices import resolve_device
from ..models import Word


class WhisperXAligner:
    def __init__(self, device: str = "auto", language: str = "en", **_ignored) -> None:
        import whisperx

        self._whisperx = whisperx
        # Alignment runs fine on CPU; only use cuda if explicitly available.
        self.device = resolve_device(device)
        if self.device == "mps":  # wav2vec2 alignment is not reliable on mps
            self.device = "cpu"
        self.language = language
        self.model, self.metadata = whisperx.load_align_model(
            language_code=language, device=self.device
        )

    def align(self, audio_path: str, text: str, language: str = "en") -> list[Word]:
        audio = self._whisperx.load_audio(audio_path)
        duration = len(audio) / 16000.0  # whisperx.load_audio resamples to 16k
        segments = [{"start": 0.0, "end": duration, "text": text.strip()}]
        result = self._whisperx.align(
            segments,
            self.model,
            self.metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        words: list[Word] = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                # Numbers/punctuation occasionally come back without timing.
                if w.get("start") is None or w.get("end") is None:
                    continue
                words.append(
                    Word(
                        word=w["word"],
                        start_ms=int(round(w["start"] * 1000)),
                        end_ms=int(round(w["end"] * 1000)),
                        score=float(w["score"]) if w.get("score") is not None else None,
                    )
                )
        return words
