#!/usr/bin/env python3
"""
Download and cache the Parakeet model
"""

import sys

try:
    import nemo.collections.asr as nemo_asr
except ImportError:
    print("Error: NeMo toolkit not installed. Run: pip install nemo_toolkit[asr]")
    sys.exit(1)


def download_model(model_name: str = "nvidia/parakeet-tdt-0.6b-v2"):
    """
    Download and cache the Parakeet model

    Args:
        model_name: HuggingFace model name
    """
    print(f"Downloading model: {model_name}")
    print("This may take a few minutes on first run...")

    try:
        # This will download and cache the model
        asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)
        print(f"✓ Model downloaded and cached successfully!")
        print(f"Model has {asr_model.num_weights / 1e6:.1f}M parameters")
        return True
    except Exception as e:
        print(f"Error downloading model: {str(e)}")
        return False


if __name__ == "__main__":
    model_name = sys.argv[1] if len(sys.argv) > 1 else "nvidia/parakeet-tdt-0.6b-v2"
    success = download_model(model_name)
    sys.exit(0 if success else 1)
