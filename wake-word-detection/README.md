# Wake Word Detection for Electron

A TypeScript implementation of wake word detection using [openWakeWord](https://github.com/dscripka/openWakeWord) with ONNX Runtime. Designed for use in Electron desktop applications.

## Overview

This project provides wake word detection capability for Electron apps, allowing you to trigger actions when a specific phrase is spoken (e.g., "Hey Jarvis", "Alexa", or a custom wake word like "Computer").

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Audio Pipeline                           │
│                                                              │
│  Microphone ──▶ 16kHz PCM ──▶ 80ms frames ──▶ Detection     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ONNX Inference Pipeline                    │
│                                                              │
│  Audio Frame ──▶ Melspectrogram ──▶ Embedding ──▶ Keyword   │
│       │              Model            Model        Model     │
│       │                                              │       │
│       └───────────▶ VAD (Voice Activity Detection) ◀─┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd wake-word-detection
npm install
npm run build
```

### System Dependencies

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install alsa-utils
```

**macOS:**
```bash
brew install sox
```

**Windows:**
Requires ffmpeg in PATH or use the Web Audio API in Electron renderer.

## Download Models

```bash
npm run download-models
```

This downloads the required ONNX models:
- `melspectrogram.onnx` - Audio preprocessing
- `embedding_model.onnx` - Feature extraction
- `silero_vad.onnx` - Voice activity detection
- Wake word models (alexa, hey_jarvis, hey_mycroft, hey_rhasspy)

## Usage

### Basic Example

```typescript
import { WakeWordDetector, NodeAudioInput } from 'wake-word-detection';

// Create detector
const detector = new WakeWordDetector({
  modelsPath: './models',
  keywords: ['hey_jarvis'],
  detectionThreshold: 0.5,
  debug: true
});

// Initialize
await detector.initialize();

// Listen for events
detector.on((event) => {
  if (event.type === 'detect') {
    console.log('Wake word detected!', event.data);
    // Start listening for user command...
  }
});

// Create audio input
const audioInput = new NodeAudioInput();

// Connect audio to detector
audioInput.onAudio(async (samples) => {
  await detector.processAudioFrame(samples);
});

// Start
detector.start();
await audioInput.start();
```

### Electron Integration

See `src/electron-integration.ts` for complete Electron integration code including:
- Main process setup
- Preload script for IPC
- Renderer process UI handling
- HTML template with visual feedback

## Available Wake Words

Pre-trained models available:
- `alexa`
- `hey_jarvis`
- `hey_mycroft`
- `hey_rhasspy`
- `timer` ("set a timer")
- `weather` ("what's the weather")

## Custom "Computer" Wake Word

The "Computer" wake word is **not available** as a pre-trained model. You have two options:

### Option 1: Train a Custom Model

Use the openWakeWord training notebook to create a custom "computer" model:

1. Open [Google Colab Training Notebook](https://github.com/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb)
2. Enter "computer" as your wake word
3. Train the model (~1 hour on free Colab)
4. Download the resulting `.onnx` file
5. Place it in your `models/` directory

### Option 2: Use Mycroft's Model

Mycroft AI has a pre-trained "computer-en" model that may be compatible:

```bash
# Download from Mycroft's model repository
# Note: Requires conversion to ONNX format
```

### Option 3: Use Alternative Wake Words

Consider using "Hey Jarvis" or training a custom phrase that's phonetically distinct (2-3 syllables recommended).

## Configuration Options

```typescript
interface WakeWordConfig {
  // Required
  modelsPath: string;           // Path to ONNX models
  keywords: string[];           // Wake words to detect

  // Optional
  detectionThreshold?: number;  // 0.0-1.0, default 0.5
  cooldownMs?: number;          // Prevents duplicate detections, default 2000
  enableVAD?: boolean;          // Voice activity detection, default true
  vadThreshold?: number;        // VAD sensitivity, default 0.5
  sampleRate?: number;          // Audio sample rate, default 16000
  frameSize?: number;           // Samples per frame, default 1280 (80ms)
  debug?: boolean;              // Enable logging, default false
}
```

## Events

```typescript
detector.on((event) => {
  switch (event.type) {
    case 'ready':
      // Detector initialized
      break;
    case 'detect':
      // Wake word detected
      // event.data: { keyword, score, timestamp, frameIndex }
      break;
    case 'speech-start':
      // Speech started (VAD)
      break;
    case 'speech-end':
      // Speech ended (VAD)
      break;
    case 'error':
      // Error occurred
      break;
  }
});
```

## Performance Notes

- Processes audio in 80ms frames
- Single CPU core can run 15-20 models simultaneously
- Detection latency: ~100-200ms
- Memory usage: ~50-100MB depending on models loaded

## Troubleshooting

### "No audio recorder found"
Install system audio tools:
```bash
# Linux
sudo apt-get install alsa-utils

# macOS
brew install sox
```

### "Model not found"
Run the model downloader:
```bash
npm run download-models
```

### Low detection accuracy
- Increase `detectionThreshold` to reduce false positives
- Decrease `detectionThreshold` to reduce false negatives
- Ensure microphone is working and positioned properly
- Reduce background noise

### High CPU usage
- Reduce number of active keywords
- Increase frame size (trades latency for efficiency)

## License

- Code: MIT
- openWakeWord pre-trained models: CC BY-NC-SA 4.0

## References

- [openWakeWord](https://github.com/dscripka/openWakeWord) - Core wake word detection framework
- [ONNX Runtime](https://onnxruntime.ai/) - ML inference engine
- [openwakeword_wasm](https://github.com/dnavarrom/openwakeword_wasm) - Browser-based implementation
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
