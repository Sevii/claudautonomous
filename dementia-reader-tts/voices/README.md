# Voices

Defines the three synthesized narrator voices. **Mute** is the fourth choice and
is a UI state (no audio) — it is added to the book manifest automatically and is
not configured here.

## Reference recordings (cloning backends)

For Chatterbox, each voice clones a reference clip placed in `refs/`:

- `refs/baritone.wav` — deep, steady, grounding
- `refs/tenor.wav` — friendly, clear, conversational
- `refs/alto.wav` — friendly, clear, conversational

Recording guidance (matches the low-arousal brief):

- ~10-20 seconds, mono WAV, ideally 24 kHz.
- Read a calm, neutral passage **slowly and warmly**, with natural pauses.
- Record all three with the **same delivery style** so the set feels cohesive.
- Quiet room, no background music or reverb.

`refs/*.wav` are git-ignored (they're large / may be talent-licensed). Keep the
source recordings and licenses tracked elsewhere.

## Preset voices (Kokoro)

Kokoro doesn't clone; it uses named presets (the `preset` field). Swap the preset
ids in `voices.example.toml` to taste — e.g. `bm_george`, `am_michael`,
`af_heart`. The `reference_audio` field is ignored by Kokoro.

## Tone knobs

| Field | Backend | Effect |
|---|---|---|
| `exaggeration` | Chatterbox | Lower = calmer, less expressive. |
| `cfg_weight` | Chatterbox | Lower = slower, steadier pacing. |
| `speed` | Kokoro | < 1.0 slows delivery. |
