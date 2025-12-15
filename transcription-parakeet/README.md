# NVIDIA Parakeet v2 Transcription - TypeScript Implementation

This project demonstrates how to use the **NVIDIA Parakeet TDT 0.6B v2** automatic speech recognition (ASR) model locally with TypeScript/Node.js.

## Overview

**Parakeet TDT 0.6B v2** is a state-of-the-art ASR model from NVIDIA featuring:
- 600 million parameters
- FastConformer-TDT architecture
- Support for long-form audio (up to 24 minutes)
- Automatic punctuation and capitalization
- Word-level timestamp predictions
- Excellent performance on spoken numbers and song lyrics

## Important: llama.cpp Compatibility

⚠️ **Parakeet models are NOT compatible with llama.cpp**

- **llama.cpp** is designed for LLM (Large Language Model) text generation models
- **Parakeet** is an ASR (Automatic Speech Recognition) model with a FastConformer-TDT architecture
- These are fundamentally different model types requiring different inference frameworks

There is an experimental [parakeet.cpp](https://github.com/jason-ni/parakeet.cpp) project attempting to implement Parakeet in GGML, but it's currently paused due to performance issues compared to native implementations.

For ASR models, use:
- **whisper.cpp** for OpenAI Whisper models
- **NVIDIA NeMo** for Parakeet models (recommended)
- **sherpa-onnx** for ONNX-based ASR inference

## Installation

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for NeMo approach)
- 2GB+ RAM for model loading

### Setup

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (for Python wrapper approach)
pip install nemo_toolkit[asr]

# Download the model (optional, will auto-download on first use)
npm run download:model
```

## Usage

This project provides two approaches:

### 1. Python Wrapper (Recommended)

Uses the official NVIDIA NeMo implementation via Python, called from TypeScript.

**Advantages:**
- ✅ Official implementation
- ✅ Full feature support
- ✅ Best performance
- ✅ Regular updates from NVIDIA

**Example:**

```typescript
import { PythonParakeetTranscriber } from './src/index.js';

const transcriber = new PythonParakeetTranscriber();

// Basic transcription
const result = await transcriber.transcribe({
  audioPath: './audio.wav',
});

console.log(result.text);

// With word timestamps
const resultWithTimestamps = await transcriber.transcribe({
  audioPath: './audio.wav',
  includeTimestamps: true,
});

console.log(resultWithTimestamps.text);
resultWithTimestamps.timestamps?.forEach(ts => {
  console.log(`${ts.word}: ${ts.start}s - ${ts.end}s`);
});
```

**Run the example:**

```bash
npm run start:python -- path/to/your/audio.wav
```

### 2. ONNX Runtime Approach

Uses ONNX-converted models with onnxruntime-node for pure TypeScript inference.

**Status:** ⚠️ Placeholder implementation

**What's needed for full implementation:**
- Audio preprocessing (resampling, mono conversion)
- Feature extraction (mel spectrogram)
- TDT decoder logic
- Integration with audio libraries

**For a working ONNX solution, consider:**
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) (C++ library with Node.js bindings)
- [onnx-asr](https://pypi.org/project/onnx-asr/) Python package with TypeScript wrapper

**Example structure:**

```typescript
import { ONNXParakeetTranscriber } from './src/index.js';

const transcriber = new ONNXParakeetTranscriber({
  encoderPath: './models/encoder.onnx',
  decoderPath: './models/decoder.onnx',
});

await transcriber.initialize();
const result = await transcriber.transcribe({ audioPath: './audio.wav' });
```

## API Reference

### TranscriptionOptions

```typescript
interface TranscriptionOptions {
  audioPath: string;              // Path to audio file (.wav, .flac)
  includeTimestamps?: boolean;    // Include word-level timestamps
  sampleRate?: number;            // Audio sample rate (default: 16000)
}
```

### TranscriptionResult

```typescript
interface TranscriptionResult {
  text: string;                   // Transcribed text
  timestamps?: WordTimestamp[];   // Optional word timestamps
}

interface WordTimestamp {
  word: string;
  start: number;                  // Start time in seconds
  end: number;                    // End time in seconds
}
```

### PythonParakeetTranscriber

```typescript
class PythonParakeetTranscriber {
  constructor(config?: ParakeetConfig);

  // Check if Python dependencies are available
  checkDependencies(): Promise<boolean>;

  // Transcribe a single audio file
  transcribe(options: TranscriptionOptions): Promise<TranscriptionResult>;

  // Batch transcribe multiple files
  transcribeBatch(files: TranscriptionOptions[]): Promise<TranscriptionResult[]>;
}
```

## Model Information

- **Model:** nvidia/parakeet-tdt-0.6b-v2
- **Architecture:** FastConformer-TDT
- **Parameters:** 600M
- **Framework:** NVIDIA NeMo
- **Input:** 16kHz monochannel audio (.wav, .flac)
- **Output:** Text with punctuation, capitalization, and optional timestamps

**HuggingFace Model Card:** https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2

## Audio Format Requirements

For best results:
- **Format:** WAV or FLAC
- **Sample Rate:** 16kHz (will be resampled if different)
- **Channels:** Mono (will be converted if stereo)
- **Bit Depth:** 16-bit recommended

You can convert audio files using ffmpeg:

```bash
# Convert to 16kHz mono WAV
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## Performance Notes

### Model Size
- Model download size: ~600MB
- Memory usage: ~2GB RAM minimum
- First run will download and cache the model

### Inference Speed
- CPU: ~2-5x realtime (depends on CPU)
- GPU (CUDA): ~20-50x realtime

## Alternative Implementations

### For Production Use

Consider these alternatives:

1. **NVIDIA NIM** - Optimized microservices for deployment
2. **NVIDIA Riva** - Enterprise speech AI platform
3. **sherpa-onnx** - C++ library with bindings for multiple languages
4. **Parakeet MLX** - For Apple Silicon devices (shows excellent performance ~0.001s inference)

## Troubleshooting

### "NeMo toolkit not installed"

```bash
pip install nemo_toolkit[asr]
```

### "Python process failed"

Check Python version:
```bash
python3 --version  # Should be 3.8+
```

### Audio file not transcribing

- Verify file format (WAV or FLAC)
- Check file exists and path is correct
- Try converting to 16kHz mono WAV

### Out of memory

- Close other applications
- Use smaller audio chunks (split long files)
- Consider using GPU if available

## Project Structure

```
transcription-parakeet/
├── src/
│   ├── index.ts              # Main exports
│   ├── types.ts              # TypeScript type definitions
│   ├── python-wrapper.ts     # Python NeMo wrapper
│   ├── python-example.ts     # Python wrapper example
│   ├── onnx-transcriber.ts   # ONNX implementation
│   └── onnx-example.ts       # ONNX example
├── scripts/
│   ├── transcribe.py         # Python transcription script
│   └── download_model.py     # Model download script
├── examples/                 # Sample audio files (add your own)
├── package.json
├── tsconfig.json
└── README.md
```

## Resources

### Documentation
- [NVIDIA Parakeet Blog Post](https://developer.nvidia.com/blog/pushing-the-boundaries-of-speech-recognition-with-nemo-parakeet-asr-models/)
- [NVIDIA NeMo Documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/models.html)
- [HuggingFace Model Card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)

### ONNX Resources
- [ONNX Community Models](https://huggingface.co/onnx-community/parakeet-tdt-0.6b-v2-ONNX)
- [sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/index.html)
- [onnx-asr Package](https://pypi.org/project/onnx-asr/)

### Related Projects
- [whisper.cpp Feature Request](https://github.com/ggml-org/whisper.cpp/issues/3118)
- [Experimental parakeet.cpp](https://github.com/jason-ni/parakeet.cpp)

## License

MIT

## Contributing

Contributions welcome! Areas for improvement:
- Full ONNX Runtime implementation with audio preprocessing
- Additional audio format support
- Performance benchmarks
- Example audio samples
- Integration with streaming audio

## Acknowledgments

- NVIDIA for developing the Parakeet models
- NeMo team for the excellent ASR framework
- HuggingFace for hosting the models and ONNX conversions
