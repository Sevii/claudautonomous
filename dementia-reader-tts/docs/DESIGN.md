# Design notes

## Why pre-render, at the sentence level

**Not word-by-word.** Prosody — the rise/fall, pacing, and pauses that make a
voice sound *unhurried, warm, and grounding* — is produced across a whole
sentence. Synthesizing one word at a time yields flat, equally-stressed, choppy
speech: the opposite of the brief, and harder for a person with dementia to
follow. It also multiplies per-request latency and cost.

**Pre-render, not on-demand.** For a curated catalogue read to dementia patients,
rendering each book once (per voice) and packaging the audio wins on the axes
that matter here:

- **Consistency** — the same familiar voice every time.
- **Reliability** — no spinner, no mid-story network failure, no anxiety.
- **Offline** — plays from local files.
- **Cost** — pay once per book, not per play.
- **Quality** — render with the best model, retry, and QA before shipping.

On-demand streaming is the right call only for user-supplied / unbounded text; a
hybrid (pre-render the catalogue, stream user content) is easy to add later.

## Word highlighting without word-by-word synthesis

The instinct toward "word by word" usually comes from wanting karaoke-style
highlighting. We get that by synthesizing the **full sentence** and then running
**forced alignment** (WhisperX) against the known text to recover per-word
timestamps. Natural prosody *and* word sync — no trade-off.

## Pipeline

```
chapter text
   │  segmenter        → paragraphs → sentences (heuristic, no heavy deps)
   ▼
for each sentence:
   │  TTS backend      → mono float32 waveform   (Chatterbox clone / Kokoro preset)
   │  forced aligner   → word timings for the clip (WhisperX)
   ▼
concatenate sentences with calming pauses, offsetting word times into
chapter-relative milliseconds
   ▼
packager → <chapter>.wav + <chapter>.json (sync map) + manifests, per book × voice
```

## Pluggability

- **TTS backends** and **aligners** are selected by name and lazy-imported, so the
  core (segmentation, packaging, dummy backend) installs and runs with no ML deps.
- A `dummy` backend + aligner render deterministic tone and evenly-spaced word
  maps — used by the tests and for front-end development without a GPU.
- Swapping in another open model (Orpheus, Parler-TTS, Piper, MeloTTS) means
  adding one `TTSBackend` subclass.

## Pacing for comprehension

Configurable silence is inserted between sentences (`--sentence-pause`, default
400 ms) and paragraphs (`--paragraph-pause`, default 800 ms). Combined with the
slowed delivery (low `cfg_weight` / `speed` < 1.0), this gives the unhurried
cadence the audience needs.

## Open items / future work

- **QA pass**: open-TTS models occasionally mispronounce names/numbers; a human
  listen-through matters more than usual for this audience.
- **Audio format**: ships WAV for fidelity; add an MP3/Opus encode step for
  distribution size.
- **Per-voice loudness normalization** (e.g. EBU R128) so all narrators match.
- **Licensing**: confirm chosen weights permit storing/redistributing generated
  audio; prefer MIT/Apache models.
