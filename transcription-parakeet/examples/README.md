# Example Audio Files

Place your audio files here for testing.

## Format Requirements

- **Supported formats:** WAV, FLAC
- **Recommended:** 16kHz, mono, 16-bit
- **Maximum duration:** Up to 24 minutes (though shorter clips recommended for testing)

## Converting Audio

Use ffmpeg to convert audio to the optimal format:

```bash
# Convert MP3 to WAV (16kHz, mono)
ffmpeg -i input.mp3 -ar 16000 -ac 1 sample.wav

# Convert any format to WAV
ffmpeg -i input.file -ar 16000 -ac 1 output.wav

# Extract audio from video
ffmpeg -i video.mp4 -ar 16000 -ac 1 -vn audio.wav
```

## Sample Audio Sources

You can find free sample audio for testing from:

1. **LibriSpeech Test Clean:**
   - https://www.openslr.org/12/
   - High-quality English speech recordings

2. **Common Voice:**
   - https://commonvoice.mozilla.org/
   - Multi-language crowd-sourced voices

3. **Free Sound:**
   - https://freesound.org/
   - Various audio clips (check licenses)

4. **Your Own Recordings:**
   - Use your phone or computer microphone
   - Record at 16kHz mono if possible
   - Save as WAV format

## Quick Test

Record a quick test using your computer:

**macOS:**
```bash
# Record 10 seconds of audio
sox -d -r 16000 -c 1 test.wav trim 0 10
```

**Linux (with arecord):**
```bash
arecord -f cd -d 10 -r 16000 -c 1 test.wav
```

**Windows (with PowerShell):**
```powershell
# Use Windows Voice Recorder app or
# Download and use ffmpeg
```

## Example Files (Not Included)

Due to file size and licensing, example audio files are not included in this repository.

Add your own files here and they will be git-ignored automatically.
