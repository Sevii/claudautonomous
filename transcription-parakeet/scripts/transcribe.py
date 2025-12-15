#!/usr/bin/env python3
"""
Python script for transcribing audio using NVIDIA Parakeet TDT 0.6B v2
This script is called by the TypeScript wrapper to perform the actual transcription.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import nemo.collections.asr as nemo_asr
except ImportError:
    print("Error: NeMo toolkit not installed. Run: pip install nemo_toolkit[asr]", file=sys.stderr)
    sys.exit(1)


def transcribe_audio(audio_path: str, model_name: str = "nvidia/parakeet-tdt-0.6b-v2",
                     include_timestamps: bool = False):
    """
    Transcribe audio file using Parakeet model

    Args:
        audio_path: Path to audio file (.wav or .flac)
        model_name: HuggingFace model name or local path
        include_timestamps: Whether to include word-level timestamps

    Returns:
        Dictionary with transcription results
    """
    # Load the model
    print(f"Loading model: {model_name}", file=sys.stderr)
    asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)

    # Transcribe
    print(f"Transcribing: {audio_path}", file=sys.stderr)

    if include_timestamps:
        output = asr_model.transcribe([audio_path], timestamps=True)
        result = {
            "text": output[0].text,
            "timestamps": []
        }

        # Extract word timestamps if available
        if hasattr(output[0], 'timestamp') and 'word' in output[0].timestamp:
            word_timestamps = output[0].timestamp['word']
            for word_info in word_timestamps:
                result["timestamps"].append({
                    "word": word_info[0],
                    "start": word_info[1],
                    "end": word_info[2]
                })
    else:
        output = asr_model.transcribe([audio_path])
        result = {
            "text": output[0].text
        }

    return result


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using Parakeet model")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--model", default="nvidia/parakeet-tdt-0.6b-v2",
                       help="Model name or path")
    parser.add_argument("--timestamps", action="store_true",
                       help="Include word-level timestamps")

    args = parser.parse_args()

    # Check if audio file exists
    if not Path(args.audio).exists():
        print(f"Error: Audio file not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    try:
        result = transcribe_audio(args.audio, args.model, args.timestamps)
        # Output JSON to stdout for the TypeScript wrapper to parse
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during transcription: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
