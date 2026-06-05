import json

from dementia_reader_tts import packager
from dementia_reader_tts.align.dummy import DummyAligner
from dementia_reader_tts.config import SynthesisConfig, VoiceConfig
from dementia_reader_tts.pipeline import Pipeline
from dementia_reader_tts.tts.dummy import DummyBackend

VOICE = VoiceConfig(id="baritone", label="Resonant Baritone", description="Deep.")
TEXT = "The morning was grey. A blackbird sang.\n\nShe smiled at the cat."


def _pipeline():
    return Pipeline(DummyBackend(sample_rate=24000), DummyAligner(), SynthesisConfig())


def test_synth_chapter_shapes():
    full, chapter = _pipeline().synth_chapter("book", "chapter-01", TEXT, VOICE)
    assert len(full) > 0
    assert chapter.voice == "baritone"
    assert chapter.audio_file == "chapter-01.wav"
    # 3 sentences across 2 paragraphs.
    assert len(chapter.sentences) == 3
    assert chapter.sentences[0].text == "The morning was grey."


def test_word_timings_monotonic_and_in_bounds():
    _, chapter = _pipeline().synth_chapter("book", "ch", TEXT, VOICE)
    prev = -1
    for sent in chapter.sentences:
        assert sent.start_ms >= prev
        prev = sent.start_ms
        assert sent.words, "every sentence should have words"
        for w in sent.words:
            assert 0 <= w.start_ms <= w.end_ms <= chapter.duration_ms
        # Words fall within their sentence span.
        assert sent.words[0].start_ms >= sent.start_ms
        assert sent.words[-1].end_ms <= sent.end_ms + 1


def test_packaging_writes_expected_files(tmp_path):
    full, chapter = _pipeline().synth_chapter("book", "chapter-01", TEXT, VOICE)
    voice_dir = tmp_path / "book" / "baritone"
    packager.write_chapter(voice_dir, full, chapter)
    packager.write_voice_manifest(voice_dir, VOICE, [chapter])
    packager.write_book_manifest(tmp_path / "book", "book", "Book", ["chapter-01"], [VOICE])

    assert (voice_dir / "chapter-01.wav").exists()
    sync = json.loads((voice_dir / "chapter-01.json").read_text())
    assert sync["sentences"][0]["words"][0]["word"]

    book = json.loads((tmp_path / "book" / "book.json").read_text())
    ids = [v["id"] for v in book["voices"]]
    assert "baritone" in ids and "mute" in ids
    mute = next(v for v in book["voices"] if v["id"] == "mute")
    assert mute["audio"] is False
