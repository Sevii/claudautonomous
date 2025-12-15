# Whisper.cpp Local Transcription with TypeScript

This project demonstrates how to use [whisper.cpp](https://github.com/ggml-org/whisper.cpp) for local audio transcription using TypeScript/Node.js.

## 🎯 What is whisper.cpp?

whisper.cpp is a high-performance C++ implementation of OpenAI's Whisper speech recognition model. Key features:

- **Runs locally** - No cloud API required, completely offline
- **No separate server needed** - Runs as a library in your application
- **Fast inference** - Optimized C++ implementation with GPU support
- **Cross-platform** - Works on macOS, Linux, Windows, iOS, Android
- **Multiple model sizes** - From tiny (75MB) to large (2.9GB)
- **Zero-cost** - No API fees, run unlimited transcriptions

## 🏗️ Architecture: Does it run separately?

**No!** whisper.cpp runs **in-process** as a library, not as a separate server.

### How it works:

```
Your Application
    ├── Load whisper.cpp library (via Node.js binding)
    ├── Load model file (e.g., ggml-base.en.bin)
    ├── Pass audio file to whisper function
    └── Get transcription result
```

The model loads into your application's memory and runs locally. No network calls, no separate processes (unless you choose to architect it that way).

## 📦 Integration Options

This repository provides examples for **three different approaches**:

### 1. nodejs-whisper (Recommended)
- ✅ Stable and production-ready
- ✅ TypeScript examples included
- ✅ Easy to use, minimal setup
- ✅ Auto-downloads models

### 2. whisper-node
- ✅ Popular with good community support
- ✅ Simple API
- ⚠️ Limited TypeScript definitions

### 3. Official addon.node
- ✅ Most up-to-date with whisper.cpp features
- ✅ Supports Voice Activity Detection (VAD)
- ✅ Best performance
- ⚠️ Requires manual compilation
- ⚠️ No TypeScript definitions

## 🚀 Quick Start

### Install Dependencies

```bash
cd transcription-whisper
npm install
```

### Run Examples

#### Option 1: Using nodejs-whisper (Easiest)

```bash
npm run example:nodejs-whisper
```

The model will auto-download on first run.

#### Option 2: Using whisper-node

```bash
npm run example:whisper-node
```

#### Option 3: Using Official Addon (Advanced)

First, build whisper.cpp:

```bash
# Clone whisper.cpp
git clone https://github.com/ggml-org/whisper.cpp
cd whisper.cpp/examples/addon.node

# Build the addon
npm install
npx cmake-js compile -T addon.node -B Release

# Download a model
cd ../..
bash models/download-ggml-model.sh base.en

# Return to project
cd ../../transcription-whisper
npm run example:official-addon
```

## 📝 API Examples

### Example 1: Basic Transcription (nodejs-whisper)

```typescript
import { nodewhisper } from 'nodejs-whisper';
import path from 'path';

const audioFile = path.resolve(__dirname, 'audio.wav');

const result = await nodewhisper(audioFile, {
  modelName: 'base.en',
  autoDownloadModelName: 'base.en',
  whisperOptions: {
    language: 'en',
    wordTimestamps: true,
    outputInSrt: true,
  },
});

console.log(result);
```

### Example 2: With Progress Callback (whisper-node)

```typescript
import whisper from 'whisper-node';

const transcript = await whisper('audio.wav', {
  modelName: 'base.en',
  whisperOptions: {
    language: 'en',
    word_timestamps: true,
  },
});

transcript.forEach(segment => {
  console.log(`[${segment.start} --> ${segment.end}]`);
  console.log(segment.speech);
});
```

### Example 3: Official Addon with VAD (Advanced)

```typescript
import { promisify } from 'util';
const { whisper } = require('./path/to/addon.node');
const whisperAsync = promisify(whisper);

const result = await whisperAsync({
  language: 'en',
  model: './models/ggml-base.en.bin',
  fname_inp: './audio.wav',
  use_gpu: true,

  // Voice Activity Detection (faster processing)
  vad: true,
  vad_model: './models/ggml-silero-v6.2.0.bin',
  vad_threshold: 0.5,

  progress_callback: (progress) => {
    console.log(`Progress: ${progress}%`);
  },
});
```

## 🎛️ Configuration Options

### Model Selection

Choose a model based on your accuracy/speed requirements:

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `tiny.en` | 75 MB | Fastest | Quick drafts, low accuracy ok |
| `base.en` | 142 MB | Fast | **Recommended for most cases** |
| `small.en` | 466 MB | Medium | Better accuracy needed |
| `medium.en` | 1.5 GB | Slow | High accuracy required |
| `large` | 2.9 GB | Slowest | Best accuracy, multilingual |

Models ending in `.en` are English-only and faster for English audio.

### Common Options

```typescript
{
  // Model
  modelName: 'base.en',              // Which model to use
  autoDownloadModelName: 'base.en',  // Auto-download if missing

  // Language
  language: 'en',                    // Input language code
  translateToEnglish: false,         // Translate to English

  // Output formats
  outputInText: false,               // Plain text
  outputInSrt: true,                 // SRT subtitles
  outputInVtt: false,                // VTT subtitles
  outputInCsv: false,                // CSV format

  // Timestamps
  wordTimestamps: true,              // Word-level timestamps
  timestamps_length: 20,             // Segment length

  // Performance
  withCuda: false,                   // GPU acceleration (requires CUDA)
  use_gpu: true,                     // Use GPU if available
}
```

## 🎤 Supported Audio Formats

whisper.cpp supports various audio formats:

- ✅ WAV (PCM 16-bit) - Native format, fastest
- ✅ MP3
- ✅ MP4 / M4A
- ✅ OGG / OGG Opus
- ✅ FLAC
- ✅ WebM

**Note:** Audio is automatically converted to 16kHz mono internally.

## 🔧 Advanced Features

### Voice Activity Detection (VAD)

VAD significantly improves performance by processing only speech segments:

```typescript
{
  vad: true,
  vad_model: './models/ggml-silero-v6.2.0.bin',
  vad_threshold: 0.5,                    // 0.0-1.0
  vad_min_speech_duration_ms: 250,
  vad_min_silence_duration_ms: 100,
}
```

Download VAD model:
```bash
cd whisper.cpp
bash models/download-vad-model.sh silero-v6.2.0
```

### GPU Acceleration

#### CUDA (NVIDIA)
```typescript
{ withCuda: true }  // nodejs-whisper
{ use_gpu: true }   // official addon
```

#### Metal (Apple Silicon)
Automatically used on macOS with Apple Silicon when available.

#### Vulkan
Supported via official addon with proper build flags.

## 📊 Performance Tips

1. **Use the right model** - Start with `base.en` and adjust as needed
2. **Enable VAD** - Can reduce processing time by 50-70%
3. **Use GPU** - 5-10x faster with CUDA/Metal
4. **Preprocess audio** - Convert to 16kHz WAV beforehand
5. **Use .en models** - Faster for English-only audio

## 🐛 Troubleshooting

### "Model not found"
Models auto-download with nodejs-whisper. For official addon, manually download:
```bash
cd whisper.cpp
bash models/download-ggml-model.sh base.en
```

### "Module not found: addon.node"
The official addon requires manual compilation. Use nodejs-whisper or whisper-node for easier setup.

### "Out of memory"
Try a smaller model (tiny or base) or increase Node.js memory:
```bash
NODE_OPTIONS=--max-old-space-size=4096 npm run example
```

### Audio format errors
Convert to WAV first:
```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## 📚 Resources

- [whisper.cpp GitHub](https://github.com/ggml-org/whisper.cpp)
- [nodejs-whisper](https://github.com/ChetanXpro/nodejs-whisper)
- [whisper-node](https://github.com/ariym/whisper-node)
- [OpenAI Whisper Paper](https://arxiv.org/abs/2212.04356)

## 🔐 Privacy & Security

All processing happens **locally** on your machine:
- ✅ No data sent to external servers
- ✅ No API keys required
- ✅ Fully offline capable
- ✅ GDPR/privacy friendly

## 📄 License

Examples are provided for educational purposes. Check individual package licenses:
- whisper.cpp: MIT License
- nodejs-whisper: MIT License
- whisper-node: MIT License
