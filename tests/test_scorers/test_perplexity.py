from unittest.mock import MagicMock, patch

import pytest

from ocrval.domain.models import ChunkInput


@pytest.fixture
def mock_lmppl():
    """Mock lmppl so tests don't need torch/transformers."""
    mock_module = MagicMock()
    mock_model = MagicMock()
    mock_module.MaskedLM.return_value = mock_model
    with patch.dict("sys.modules", {"lmppl": mock_module}):
        yield mock_model


def _make_scorer(mock_lmppl, **kwargs):
    """Import and instantiate after mock is in place."""
    from ocrval.scorers.perplexity import PerplexityScorer

    return PerplexityScorer(**kwargs)


def test_clean_text_low_ppl(mock_lmppl, good_chunk):
    mock_lmppl.get_perplexity.return_value = [15.0]
    scorer = _make_scorer(mock_lmppl)
    result = scorer.score(good_chunk)
    assert result.score > 0.9
    assert result.value == 15.0


def test_garbage_text_high_ppl(mock_lmppl, bad_chunk):
    mock_lmppl.get_perplexity.return_value = [120.0]
    scorer = _make_scorer(mock_lmppl)
    result = scorer.score(bad_chunk)
    assert result.score == 0.0
    assert result.value == 120.0


def test_empty_text_skipped(mock_lmppl, empty_chunk):
    scorer = _make_scorer(mock_lmppl)
    result = scorer.score(empty_chunk)
    assert result.score == 1.0
    assert result.value is None
    mock_lmppl.get_perplexity.assert_not_called()


def test_short_text_skipped(mock_lmppl):
    chunk = ChunkInput(ref="#/x", label="p", text="OK merci")
    scorer = _make_scorer(mock_lmppl)
    result = scorer.score(chunk)
    assert result.score == 1.0
    assert result.value is None


def test_normalization_midpoint(mock_lmppl, good_chunk):
    mock_lmppl.get_perplexity.return_value = [55.0]
    scorer = _make_scorer(mock_lmppl, ppl_floor=10.0, ppl_ceiling=100.0)
    result = scorer.score(good_chunk)
    assert abs(result.score - 0.5) < 0.01


def test_normalization_floor(mock_lmppl, good_chunk):
    mock_lmppl.get_perplexity.return_value = [5.0]
    scorer = _make_scorer(mock_lmppl, ppl_floor=10.0, ppl_ceiling=100.0)
    result = scorer.score(good_chunk)
    assert result.score == 1.0


def test_import_error_without_extra():
    with patch.dict("sys.modules", {"lmppl": None}):
        with pytest.raises(ImportError, match="\\[llm\\] extra"):
            from ocrval.scorers.perplexity import PerplexityScorer

            PerplexityScorer()
