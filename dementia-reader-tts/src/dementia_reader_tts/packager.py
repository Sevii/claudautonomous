"""Write the packaged output: per book x voice audio + sync maps + manifests.

Output layout:
    output/<book-id>/
        book.json                 # title, chapter list, available voices (+ Mute)
        <voice-id>/
            manifest.json         # voice metadata + chapter index
            <chapter-id>.wav      # chapter audio
            <chapter-id>.json     # ChapterAudio sync map (sentences + words)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import audio as audio_utils
from .config import VoiceConfig
from .models import ChapterAudio

# "Mute" is a UI state, not a synthesized voice - surfaced here so the app can
# render the full set of narrator choices from one manifest.
MUTE_VOICE = {"id": "mute", "label": "Mute", "description": "Text only, no audio.", "audio": False}


def write_chapter(
    voice_dir: Path,
    full_audio: np.ndarray,
    chapter: ChapterAudio,
) -> None:
    voice_dir.mkdir(parents=True, exist_ok=True)
    audio_utils.save_wav(voice_dir / chapter.audio_file, full_audio, chapter.sample_rate)
    (voice_dir / f"{chapter.chapter}.json").write_text(
        json.dumps(chapter.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_voice_manifest(
    voice_dir: Path,
    voice: VoiceConfig,
    chapters: list[ChapterAudio],
) -> None:
    manifest = {
        "voice": {
            "id": voice.id,
            "label": voice.label,
            "description": voice.description,
        },
        "sample_rate": chapters[0].sample_rate if chapters else None,
        "chapters": [
            {
                "id": c.chapter,
                "audio": c.audio_file,
                "sync_map": f"{c.chapter}.json",
                "duration_ms": c.duration_ms,
            }
            for c in chapters
        ],
    }
    (voice_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def write_book_manifest(
    book_dir: Path,
    book_id: str,
    title: str,
    chapter_ids: list[str],
    voices: list[VoiceConfig],
) -> None:
    book_dir.mkdir(parents=True, exist_ok=True)
    voice_entries = [
        {"id": v.id, "label": v.label, "description": v.description, "audio": True}
        for v in voices
    ]
    voice_entries.append(dict(MUTE_VOICE))
    manifest = {
        "id": book_id,
        "title": title,
        "chapters": chapter_ids,
        "voices": voice_entries,
    }
    (book_dir / "book.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
