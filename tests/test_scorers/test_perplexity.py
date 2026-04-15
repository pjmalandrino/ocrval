import math
from unittest.mock import MagicMock, patch

import pytest

from ocrval.domain.models import ChunkInput


@pytest.fixture
def mock_transformers():
    """Mock torch + transformers so tests don't need heavy deps."""
    mock_torch = MagicMock()
    mock_tf = MagicMock()

    # Make torch.no_grad() work as context manager
    mock_torch.no_grad.return_value.__enter__ = MagicMock()
    mock_torch.no_grad.return_value.__exit__ = MagicMock()

    with patch.dict("sys.modules", {"torch": mock_torch, "transformers": mock_tf}):
        yield mock_torch, mock_tf


def _make_scorer(mock_transformers, ppl_value=25.0, **kwargs):
    """Build a PerplexityScorer with _compute_pseudo_ppl mocked to return a fixed value."""
    from ocrval.scorers.perplexity import PerplexityScorer

    scorer = PerplexityScorer.__new__(PerplexityScorer)
    scorer._ceiling = kwargs.get("ppl_ceiling", 100.0)
    scorer._floor = kwargs.get("ppl_floor", 10.0)
    scorer._tokenizer = MagicMock()
    scorer._model = MagicMock()
    scorer._torch = mock_transformers[0]

    # Mock the heavy computation
    scorer._compute_pseudo_ppl = MagicMock(return_value=ppl_value)
    return scorer


def test_clean_text_low_ppl(mock_transformers, good_chunk):
    scorer = _make_scorer(mock_transformers, ppl_value=15.0)
    result = scorer.score(good_chunk)
    assert result.score > 0.9
    assert result.value == 15.0


def test_garbage_text_high_ppl(mock_transformers, bad_chunk):
    scorer = _make_scorer(mock_transformers, ppl_value=120.0)
    result = scorer.score(bad_chunk)
    assert result.score == 0.0
    assert result.value == 120.0


def test_empty_text_skipped(mock_transformers, empty_chunk):
    scorer = _make_scorer(mock_transformers)
    result = scorer.score(empty_chunk)
    assert result.score == 1.0
    assert result.value is None
    scorer._compute_pseudo_ppl.assert_not_called()


def test_short_text_skipped(mock_transformers):
    chunk = ChunkInput(ref="#/x", label="p", text="OK merci")
    scorer = _make_scorer(mock_transformers)
    result = scorer.score(chunk)
    assert result.score == 1.0
    assert result.value is None


def test_normalization_midpoint(mock_transformers, good_chunk):
    scorer = _make_scorer(mock_transformers, ppl_value=55.0, ppl_floor=10.0, ppl_ceiling=100.0)
    result = scorer.score(good_chunk)
    assert abs(result.score - 0.5) < 0.01


def test_normalization_floor(mock_transformers, good_chunk):
    scorer = _make_scorer(mock_transformers, ppl_value=5.0, ppl_floor=10.0, ppl_ceiling=100.0)
    result = scorer.score(good_chunk)
    assert result.score == 1.0


def test_import_error_without_extra():
    with patch.dict("sys.modules", {"torch": None, "transformers": None}):
        with pytest.raises(ImportError, match="\\[llm\\] extra"):
            from ocrval.scorers.perplexity import PerplexityScorer

            PerplexityScorer()
