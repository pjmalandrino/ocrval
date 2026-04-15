from ocrval.domain.models import ChunkInput
from ocrval.scorers.special_char import SpecialCharScorer


def test_clean_text(good_chunk):
    scorer = SpecialCharScorer(threshold=0.15)
    result = scorer.score(good_chunk)
    assert result.score > 0.8
    assert result.value < 0.05


def test_dirty_text(bad_chunk):
    scorer = SpecialCharScorer(threshold=0.15)
    result = scorer.score(bad_chunk)
    assert result.score < 0.5


def test_empty_text(empty_chunk):
    scorer = SpecialCharScorer(threshold=0.15)
    result = scorer.score(empty_chunk)
    assert result.score == 0.0


def test_no_alpha():
    chunk = ChunkInput(ref="#/x", label="p", text="123 456 789")
    scorer = SpecialCharScorer(threshold=0.15)
    result = scorer.score(chunk)
    assert result.score == 0.0
