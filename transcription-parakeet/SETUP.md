# Setup Guide

## Quick Start

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Install Python Dependencies

The Python wrapper approach requires NVIDIA NeMo toolkit:

```bash
# Using pip
pip install nemo_toolkit[asr]

# Or using pip3
pip3 install nemo_toolkit[asr]
```

### 3. Download the Model (Optional)

The model will auto-download on first use, but you can pre-download it:

```bash
npm run download:model
```

Or manually:

```bash
python3 scripts/download_model.py
```

### 4. Prepare Audio Files

Place your audio files in the `examples/` directory or specify the path when running.

**Recommended format:**
- WAV or FLAC
- 16kHz sample rate
- Mono (single channel)

**Convert audio with ffmpeg:**

```bash
# Install ffmpeg (if not already installed)
# Ubuntu/Debian: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from https://ffmpeg.org/

# Convert to optimal format
ffmpeg -i input.mp3 -ar 16000 -ac 1 examples/sample.wav
```

### 5. Run Examples

**Python wrapper example:**

```bash
# Build TypeScript
npm run build

# Run with your audio file
npm run start:python -- examples/sample.wav

# Or directly with node
node dist/python-example.js examples/sample.wav
```

**ONNX example (placeholder):**

```bash
npm run start:onnx
```

## Detailed Setup

### System Requirements

**Minimum:**
- Node.js 18+
- Python 3.8+
- 2GB RAM
- 1GB disk space

**Recommended:**
- Node.js 20+
- Python 3.10+
- 4GB RAM
- NVIDIA GPU with CUDA support (for faster inference)
- 2GB disk space

### Python Environment Setup

#### Option 1: System Python

```bash
pip3 install nemo_toolkit[asr]
```

#### Option 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install nemo_toolkit[asr]
```

#### Option 3: Conda

```bash
# Create conda environment
conda create -n parakeet python=3.10
conda activate parakeet

# Install dependencies
pip install nemo_toolkit[asr]
```

### Verify Installation

```bash
# Check Node.js
node --version  # Should be 18+

# Check Python
python3 --version  # Should be 3.8+

# Check NeMo installation
python3 -c "import nemo.collections.asr; print('NeMo OK')"

# Check TypeScript compilation
npm run build
```

## GPU Support (Optional)

For faster inference with NVIDIA GPUs:

### 1. Install CUDA Toolkit

Download from: https://developer.nvidia.com/cuda-downloads

Recommended version: CUDA 11.8 or 12.1

### 2. Install PyTorch with CUDA

```bash
# For CUDA 11.8
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Verify GPU Support

```bash
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Troubleshooting

### Issue: "nemo_toolkit not found"

**Solution:**
```bash
pip3 install nemo_toolkit[asr]
# Or with specific version
pip3 install "nemo_toolkit[asr]>=2.0.0"
```

### Issue: "Cannot find module 'onnxruntime-node'"

**Solution:**
```bash
npm install
```

### Issue: Python script fails

**Check Python path:**
```bash
which python3
python3 --version
```

**Update the script path in `python-wrapper.ts` if needed.**

### Issue: Out of memory

**Solutions:**
- Close other applications
- Split large audio files into smaller chunks
- Use GPU inference if available
- Increase system swap space

### Issue: Model download fails

**Try manual download:**
```bash
python3 << EOF
import nemo.collections.asr as nemo_asr
model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
print("Model downloaded successfully")
EOF
```

### Issue: Audio file not supported

**Convert to WAV:**
```bash
ffmpeg -i input.file -ar 16000 -ac 1 output.wav
```

## Next Steps

1. Try the examples with your own audio files
2. Integrate into your application
3. Explore batch processing for multiple files
4. Consider deploying with NVIDIA NIM for production

## Additional Resources

- [NVIDIA NeMo Documentation](https://docs.nvidia.com/nemo-framework/)
- [Parakeet Model Card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Node.js Documentation](https://nodejs.org/docs/)

## Getting Help

If you encounter issues:

1. Check the Troubleshooting section above
2. Review the main [README.md](README.md)
3. Check NVIDIA NeMo documentation
4. Open an issue on GitHub

## Development

### Build TypeScript

```bash
npm run build
```

### Watch mode for development

```bash
npx tsc --watch
```

### Run with ts-node (development)

```bash
npx ts-node src/python-example.ts examples/sample.wav
```
