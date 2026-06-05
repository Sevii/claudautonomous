from dementia_reader_tts.segmenter import segment, split_sentences


def test_basic_sentence_split():
    s = split_sentences("Hello there. How are you? I am fine!")
    assert s == ["Hello there.", "How are you?", "I am fine!"]


def test_abbreviation_not_split():
    s = split_sentences("Mr. Bell fed the cat. He purred.")
    assert s == ["Mr. Bell fed the cat.", "He purred."]


def test_paragraphs_preserved():
    text = "First one. Second one.\n\nNew paragraph here."
    paras = segment(text)
    assert len(paras) == 2
    assert paras[0] == ["First one.", "Second one."]
    assert paras[1] == ["New paragraph here."]


def test_empty_and_whitespace():
    assert segment("") == []
    assert segment("   \n\n   ") == []


def test_quotes_and_brackets():
    s = split_sentences('"Stop," she said. He stopped.')
    assert s == ['"Stop," she said.', "He stopped."]
