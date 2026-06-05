"""Command-line entry point.

Example (runs anywhere, no GPU / no downloads):
    dementia-reader-tts synth --book examples/sample_book --out output \\
        --backend dummy --aligner dummy

Production (workstation pre-render):
    dementia-reader-tts synth --book my-book --out output \\
        --backend chatterbox --aligner whisperx --voices voices/voices.toml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .book import load_book
from .config import SynthesisConfig, load_voices
from .pipeline import Pipeline


def _synth(args: argparse.Namespace) -> int:
    book = load_book(args.book)
    voices = load_voices(args.voices)
    if args.voice_id:
        wanted = set(args.voice_id)
        voices = [v for v in voices if v.id in wanted]
        if not voices:
            print(f"No voices match {sorted(wanted)}", file=sys.stderr)
            return 2

    config = SynthesisConfig(
        backend=args.backend,
        aligner=args.aligner,
        language=args.language,
        device=args.device,
        sentence_pause_ms=args.sentence_pause,
        paragraph_pause_ms=args.paragraph_pause,
    )

    # Import here so --help works without the heavy ML extras installed.
    from .tts.base import get_backend
    from .align.base import get_aligner
    from . import packager

    print(f"Book: {book.title!r} ({len(book.chapters)} chapters)")
    print(f"Backend={config.backend}  Aligner={config.aligner}  Device={config.device}")
    print(f"Voices: {', '.join(v.id for v in voices)}  (+ mute UI state)")

    tts = get_backend(config.backend, device=config.device, sample_rate=args.sample_rate)
    aligner = get_aligner(config.aligner, device=config.device, language=config.language)
    pipeline = Pipeline(tts, aligner, config)

    out_root = Path(args.out)
    book_dir = out_root / book.id

    for voice in voices:
        voice_dir = book_dir / voice.id
        produced = []
        for chapter in book.chapters:
            print(f"  [{voice.id}] {chapter.id} ...", flush=True)
            full, meta = pipeline.synth_chapter(book.id, chapter.id, chapter.text, voice)
            packager.write_chapter(voice_dir, full, meta)
            produced.append(meta)
        packager.write_voice_manifest(voice_dir, voice, produced)

    packager.write_book_manifest(
        book_dir, book.id, book.title, [c.id for c in book.chapters], voices
    )
    print(f"Done -> {book_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dementia-reader-tts")
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("synth", help="Render a book to audio + word sync maps.")
    s.add_argument("--book", required=True, help="Path to a book directory of chapter .txt files.")
    s.add_argument("--out", default="output", help="Output root directory (default: output).")
    s.add_argument(
        "--voices",
        default="voices/voices.example.toml",
        help="TOML file of [[voice]] definitions.",
    )
    s.add_argument(
        "--voice-id",
        action="append",
        help="Only render this voice id (repeatable). Default: all.",
    )
    s.add_argument("--backend", default="chatterbox", choices=["chatterbox", "kokoro", "dummy"])
    s.add_argument("--aligner", default="whisperx", choices=["whisperx", "dummy"])
    s.add_argument("--language", default="en")
    s.add_argument("--device", default="auto", help="auto | cpu | cuda | mps")
    s.add_argument("--sample-rate", type=int, default=24000, help="Used by dummy backend only.")
    s.add_argument("--sentence-pause", type=int, default=400, help="ms of silence between sentences.")
    s.add_argument("--paragraph-pause", type=int, default=800, help="ms of silence between paragraphs.")
    s.set_defaults(func=_synth)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
