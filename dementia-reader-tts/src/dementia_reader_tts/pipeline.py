"""Orchestration: chapter text + voice -> chapter audio + word sync map.

For each sentence we (1) synthesize audio, (2) force-align the known text to get
word timings, then concatenate sentences with calming pauses between them,
offsetting every word's timing into chapter-relative milliseconds.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from . import audio as audio_utils
from .align.base import Aligner
from .config import SynthesisConfig, VoiceConfig
from .models import ChapterAudio, Sentence, Word
from .segmenter import segment
from .tts.base import TTSBackend


class Pipeline:
    def __init__(
        self,
        tts: TTSBackend,
        aligner: Aligner,
        config: SynthesisConfig,
    ) -> None:
        self.tts = tts
        self.aligner = aligner
        self.config = config

    def synth_chapter(
        self,
        book_id: str,
        chapter_id: str,
        text: str,
        voice: VoiceConfig,
    ) -> tuple[np.ndarray, ChapterAudio]:
        sr = self.tts.sample_rate
        paragraphs = segment(text)

        chunks: list[np.ndarray] = []
        sentences: list[Sentence] = []
        cursor_ms = 0
        index = 0

        for p_idx, para in enumerate(paragraphs):
            last_para = p_idx == len(paragraphs) - 1
            for s_idx, sent in enumerate(para):
                clip = self.tts.synthesize(sent, voice)
                words = self._align_clip(clip, sent, sr, offset_ms=cursor_ms)
                clip_ms = audio_utils.duration_ms(clip, sr)

                sentences.append(
                    Sentence(
                        index=index,
                        text=sent,
                        start_ms=cursor_ms,
                        end_ms=cursor_ms + clip_ms,
                        words=words,
                    )
                )
                chunks.append(clip)
                cursor_ms += clip_ms
                index += 1

                last_sentence = last_para and s_idx == len(para) - 1
                if last_sentence:
                    pause_ms = 0  # no trailing silence at the very end
                elif s_idx == len(para) - 1:
                    pause_ms = self.config.paragraph_pause_ms
                else:
                    pause_ms = self.config.sentence_pause_ms

                if pause_ms:
                    chunks.append(audio_utils.silence(pause_ms, sr))
                    cursor_ms += pause_ms

        full = audio_utils.concat(chunks)
        chapter = ChapterAudio(
            book=book_id,
            chapter=chapter_id,
            voice=voice.id,
            audio_file=f"{chapter_id}.wav",
            sample_rate=sr,
            duration_ms=audio_utils.duration_ms(full, sr),
            sentences=sentences,
        )
        return full, chapter

    def _align_clip(
        self, clip: np.ndarray, text: str, sr: int, offset_ms: int
    ) -> list[Word]:
        """Align one sentence clip and shift word times into chapter coordinates."""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            audio_utils.save_wav(tmp_path, clip, sr)
            local = self.aligner.align(str(tmp_path), text, self.config.language)
        finally:
            tmp_path.unlink(missing_ok=True)

        return [
            Word(
                word=w.word,
                start_ms=w.start_ms + offset_ms,
                end_ms=w.end_ms + offset_ms,
                score=w.score,
            )
            for w in local
        ]
