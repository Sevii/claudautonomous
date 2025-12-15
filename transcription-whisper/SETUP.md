# Setup Guide

## Quick Setup (Recommended)

### 1. Install Dependencies

```bash
cd transcription-whisper
npm install
```

### 2. Prepare Sample Audio

Place a sample audio file in `examples/sample-audio.wav` or update the paths in the example files.

You can convert any audio file to the correct format using ffmpeg:

```bash
mkdir -p examples
ffmpeg -i your-audio-file.mp3 -ar 16000 -ac 1 examples/sample-audio.wav
```

### 3. Run an Example

**Easiest option (nodejs-whisper):**
```bash
npm run example:nodejs-whisper
```

The model will automatically download on first run (~142 MB for base.en).

## Approach Comparison

| Feature | nodejs-whisper | whisper-node | Official Addon |
|---------|----------------|--------------|----------------|
| Setup Difficulty | ⭐ Easy | ⭐ Easy | ⭐⭐⭐ Hard |
| TypeScript Support | ✅ Yes | ⚠️ Partial | ❌ No |
| Auto-download Models | ✅ Yes | ✅ Yes | ❌ Manual |
| Compilation Required | ❌ No | ❌ No | ✅ Yes |
| VAD Support | ❌ No | ❌ No | ✅ Yes |
| Latest Features | ⚠️ Delayed | ⚠️ Delayed | ✅ Immediate |
| Production Ready | ✅ Yes | ✅ Yes | ✅ Yes |
| Recommended For | General use | Simple projects | Advanced users |

## Advanced Setup: Official Addon

If you need the latest features or VAD support:

### 1. Install Build Tools

**macOS:**
```bash
brew install cmake
xcode-select --install
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
```

**Windows:**
- Install Visual Studio 2019+ with C++ tools
- Install CMake

### 2. Clone and Build whisper.cpp

```bash
# Clone the repository
git clone https://github.com/ggml-org/whisper.cpp
cd whisper.cpp

# Build the addon
cd examples/addon.node
npm install
npx cmake-js compile -T addon.node -B Release

# Download models
cd ../..
bash models/download-ggml-model.sh base.en

# Optional: Download VAD model for faster processing
bash models/download-vad-model.sh silero-v6.2.0
```

### 3. Update Example Paths

Edit `src/example-official-addon.ts` and update the paths:

```typescript
const addonPath = path.join(
  __dirname,
  '../../../whisper.cpp/build/Release/addon.node'
);

const modelPath = path.join(
  __dirname,
  '../../../whisper.cpp/models/ggml-base.en.bin'
);
```

### 4. Run the Example

```bash
cd transcription-whisper
npm run example:official-addon
```

## GPU Acceleration

### NVIDIA CUDA

1. Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

2. For nodejs-whisper:
```typescript
await nodewhisper(audioFile, {
  withCuda: true,
  // ... other options
});
```

3. For official addon, rebuild with CUDA:
```bash
cd whisper.cpp/examples/addon.node
GGML_CUDA=1 npx cmake-js compile -T addon.node -B Release
```

### Apple Metal (macOS)

Metal support is automatic on Apple Silicon Macs. No additional setup required.

### Vulkan

For official addon only:

```bash
cd whisper.cpp/examples/addon.node
GGML_VULKAN=1 npx cmake-js compile -T addon.node -B Release
```

## Downloading Models Manually

Models are stored in different locations depending on the package:

### nodejs-whisper
Models auto-download to `~/.cache/whisper` on first use.

### whisper-node
Models auto-download to the package directory.

### Official Addon
Download manually:

```bash
cd whisper.cpp
bash models/download-ggml-model.sh [model-name]
```

Available models:
- `tiny`, `tiny.en`
- `base`, `base.en`
- `small`, `small.en`
- `medium`, `medium.en`
- `large-v1`, `large-v2`, `large-v3`

Or download directly from Hugging Face:
```bash
# Example: base.en model
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
```

## Testing Your Setup

Create a simple test file:

```typescript
// test.ts
import { nodewhisper } from 'nodejs-whisper';

async function test() {
  const result = await nodewhisper('examples/sample-audio.wav', {
    modelName: 'tiny.en',
    autoDownloadModelName: 'tiny.en',
  });
  console.log('Success!', result);
}

test();
```

Run it:
```bash
npx ts-node test.ts
```

If you see transcription output, everything is working!

## Common Issues

### Build Fails on macOS
```bash
# Install Xcode command line tools
xcode-select --install

# Install cmake
brew install cmake
```

### Build Fails on Linux
```bash
# Install build tools
sudo apt-get install build-essential cmake

# Update cmake if needed
sudo snap install cmake --classic
```

### Build Fails on Windows
- Ensure Visual Studio 2019 or later is installed
- Install "Desktop development with C++" workload
- Install CMake from https://cmake.org/download/

### Node.js Out of Memory
```bash
# Increase memory limit
export NODE_OPTIONS=--max-old-space-size=4096
npm run example:nodejs-whisper
```

## Next Steps

1. ✅ Run the examples with your own audio files
2. ✅ Experiment with different models and options
3. ✅ Integrate transcription into your application
4. ✅ Set up GPU acceleration for faster processing
5. ✅ Try VAD for improved performance on long audio files

For more details, see [README.md](README.md).
