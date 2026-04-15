from ocrval.scorers.short_chunk import ShortChunkScorer


def test_normal_text(good_chunk):
    scorer = ShortChunkScorer(min_words=3)
    result = scorer.score(good_chunk)
    assert result.score == 1.0
    assert result.value is False


def test_empty(empty_chunk):
    scorer = ShortChunkScorer(min_words=3)
    result = scorer.score(empty_chunk)
    assert result.score == 0.0
    assert result.value is True


def test_short(short_chunk):
    scorer = ShortChunkScorer(min_words=3)
    result = scorer.score(short_chunk)
    assert result.score == 0.3
    assert result.value is True
