"""Shared device resolution for torch-backed components."""

from __future__ import annotations


def resolve_device(requested: str = "auto") -> str:
    """Resolve "auto" to the best available torch device.

    Falls back to "cpu" if torch is not importable (e.g. dummy-only runs).
    """

    if requested and requested != "auto":
        return requested
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"
