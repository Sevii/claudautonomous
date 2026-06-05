"""Lightweight, dependency-free text segmentation.

Splits a chapter into paragraphs (blank-line separated) and each paragraph into
sentences. This is a heuristic regex segmenter with a small abbreviation guard -
good enough for prose, and it avoids pulling in nltk/spacy. Swap in a real
sentence tokenizer here if you need stronger handling of edge cases.
"""

from __future__ import annotations

import re

# Abbreviations that end in '.' but do not end a sentence.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
    "inc", "ltd", "co", "no", "vol", "fig", "approx", "dept", "gen",
    "e.g", "i.e", "a.m", "p.m",
}

# A sentence boundary: terminal punctuation, optional closing quote/bracket,
# whitespace, then a capital letter / quote / digit starting the next sentence.
_BOUNDARY = re.compile(r'([.!?]+["\')\]]?)\s+(?=["\'(\[]?[A-Z0-9])')

_WHITESPACE = re.compile(r"[ \t]+")


def _last_token(text: str) -> str:
    text = text.rstrip(".!?\"')]")
    match = re.search(r"([A-Za-z.]+)$", text)
    return match.group(1).lower() if match else ""


def split_sentences(paragraph: str) -> list[str]:
    """Split a single paragraph (no blank lines) into sentences."""

    paragraph = _WHITESPACE.sub(" ", paragraph.replace("\n", " ")).strip()
    if not paragraph:
        return []

    sentences: list[str] = []
    start = 0
    for match in _BOUNDARY.finditer(paragraph):
        candidate = paragraph[start:match.end(1)].strip()
        # Don't break right after a known abbreviation ("Dr. Smith").
        if _last_token(candidate) in _ABBREVIATIONS:
            continue
        if candidate:
            sentences.append(candidate)
        start = match.end()

    tail = paragraph[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def segment(text: str) -> list[list[str]]:
    """Segment chapter text into paragraphs, each a list of sentences."""

    paragraphs: list[list[str]] = []
    for block in re.split(r"\n\s*\n", text):
        sentences = split_sentences(block)
        if sentences:
            paragraphs.append(sentences)
    return paragraphs
