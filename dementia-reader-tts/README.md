# dementia-reader-tts

Pre-render narrated audiobooks for a **dementia reading app**, using **open-weights
TTS** and **forced alignment** for word-level highlighting.

Given a book (chapters of plain text) and a set of narrator voices, this tool
produces, **per book × voice**:

- a chapter audio file (`.wav`), and
- a **word-level sync map** (`.json`) so the app can highlight each word as it's read.

It deliberately renders **ahead of time** at the **sentence** level (never word
by word — that destroys the calm, unhurried prosody the brief calls for). See
[`docs/DESIGN.md`](docs/DESIGN.md) for the rationale.

## Why this shape

- **Voices:** four narrator choices — **Mute**, **Resonant Baritone**, **Warm
  Tenor**, **Friendly Alto**. *Mute* is a UI state (no audio); the other three are
  synthesized with a calm, low-arousal delivery.
- **TTS:** [Chatterbox](https://github.com/resemble-ai/chatterbox) (MIT) clones a
  short calm reference recording per voice — top quality for workstation
  pre-render. [Kokoro](https://github.com/hexgrad/kokoro) (Apache-2.0) is the tiny
  CPU / on-device alternative using preset voices.
- **Timestamps:** [WhisperX](https://github.com/m-bain/whisperX) forced alignment
  turns each synthesized sentence (whose text we already know) into accurate word
  timings — the same Whisper/Parakeet alignment stack already used elsewhere in
  this repo.
- **Output:** plain files an app can ship or stream, fully offline.

## Install

Uses [uv](https://docs.astral.sh/uv/).

```bash
cd dementia-reader-tts

# Core only (segmentation, packaging, dummy backend — runs anywhere):
uv sync

# Add the real backends as needed:
uv sync --extra chatterbox   # high-quality cloning TTS (torch)
uv sync --extra kokoro       # tiny CPU / on-device TTS
uv sync --extra align        # WhisperX word timestamps (needs ffmpeg on PATH)
uv sync --extra dev          # pytest
```

> **ffmpeg** is required by the `whisperx` aligner (it loads audio via ffmpeg).
> Install it from your OS package manager.

## Quick start (no GPU, no downloads)

The `dummy` backend + aligner exercise the entire pipeline offline, so you can
see the output shape immediately:

```bash
uv run dementia-reader-tts synth \
  --book examples/sample_book \
  --out output \
  --backend dummy --aligner dummy
```

This writes:

```
output/the-quiet-garden/
├── book.json                 # title, chapters, voices (incl. Mute)
├── baritone/
│   ├── manifest.json
│   ├── chapter-01.wav
│   ├── chapter-01.json       # sync map: sentences + per-word timings
│   └── chapter-02.{wav,json}
├── tenor/   ...
└── alto/    ...
```

## Production render

1. Record a short, calm reference clip for each voice (~10-20s, mono WAV) and
   point `voices/voices.example.toml` at them (`reference_audio = ...`). For a
   consistent "house style", record all three with the same slow, warm delivery.
2. Render with the real backends:

```bash
uv run dementia-reader-tts synth \
  --book path/to/my-book \
  --out output \
  --backend chatterbox \
  --aligner whisperx \
  --voices voices/voices.example.toml \
  --device auto
```

On-device / CPU path instead:

```bash
uv run dementia-reader-tts synth --book path/to/my-book \
  --backend kokoro --aligner whisperx --device cpu
```

### Useful flags

| Flag | Meaning |
|---|---|
| `--voice-id baritone` | Render only one voice (repeatable). |
| `--sentence-pause 400` | ms of silence between sentences (pacing). |
| `--paragraph-pause 800` | ms of silence between paragraphs. |
| `--device cpu\|cuda\|mps\|auto` | Compute device. |

## Sync map format

`output/<book>/<voice>/<chapter>.json`:

```json
{
  "book": "the-quiet-garden",
  "chapter": "chapter-01",
  "voice": "baritone",
  "audio_file": "chapter-01.wav",
  "sample_rate": 24000,
  "duration_ms": 18420,
  "sentences": [
    {
      "index": 0,
      "text": "The morning was soft and grey.",
      "start_ms": 0,
      "end_ms": 2300,
      "words": [
        { "word": "The", "start_ms": 150, "end_ms": 360, "score": 0.98 }
      ]
    }
  ]
}
```

The app plays `audio_file` and highlights each word when playback passes its
`start_ms`. **Mute** simply hides the player and shows text only.

## Book input format

A directory of chapter `.txt` files. Optional `book.toml`:

```toml
id = "the-quiet-garden"
title = "The Quiet Garden"
chapters = ["chapter-01.txt", "chapter-02.txt"]   # omit to use sorted *.txt
```

## Project layout

```
src/dementia_reader_tts/
├── segmenter.py     text -> paragraphs -> sentences (heuristic, no heavy deps)
├── tts/             TTS backends: chatterbox, kokoro, dummy (lazy-imported)
├── align/           aligners: whisperx, dummy
├── pipeline.py      sentence synth + align + concat with calming pauses
├── packager.py      writes audio + sync maps + manifests
├── book.py          load a book directory
└── cli.py           `dementia-reader-tts synth ...`
```

## Tests

```bash
uv run --extra dev pytest
```

## Licensing note

For a shipping app, stick to MIT/Apache-licensed model weights (Chatterbox,
Kokoro, Piper, MeloTTS). Avoid non-commercial-licensed weights (e.g. XTTS-v2's
Coqui license). Confirm your chosen model permits **storing and redistributing**
generated audio.
