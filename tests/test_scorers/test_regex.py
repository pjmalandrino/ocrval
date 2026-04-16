"""Tests for RegexScorer — built-in and custom pattern detection."""

from ocrval.domain.models import ChunkInput
from ocrval.scorers.regex import BUILTIN_PATTERNS, RegexScorer


def _chunk(text: str) -> ChunkInput:
    return ChunkInput(ref="#/texts/0", label="paragraph", page_no=1, text=text)


# ── Built-in patterns ───────────────────────────────────────────────────


def test_clean_text_no_artifacts():
    scorer = RegexScorer()
    result = scorer.score(_chunk("Le montant total de la facture est de mille deux cents euros."))
    assert result.score == 1.0
    assert result.value == 0


def test_pipe_as_letter():
    """Pipe character used as l/I: 'app|icable'."""
    scorer = RegexScorer()
    result = scorer.score(_chunk("Les conditions sont app|icab|es à toutes |es commandes."))
    assert result.value > 0
    assert result.score < 1.0


def test_currency_as_letter():
    """€ used as e: 'g€n€ral€s'."""
    scorer = RegexScorer()
    result = scorer.score(_chunk("L€s cond€tions g€n€ral€s d€ v€nt€"))
    assert result.value > 0
    assert result.score < 1.0


def test_at_as_letter():
    """@ used as a: 'comm@ndes'."""
    scorer = RegexScorer()
    result = scorer.score(_chunk("Les comm@ndes sont v@lid@bles"))
    assert result.value > 0
    assert result.score < 1.0


def test_garbage_sequence():
    """3+ consecutive non-standard characters."""
    scorer = RegexScorer()
    result = scorer.score(_chunk("Texte normal §†‡§†‡ suite du texte"))
    assert result.value > 0
    assert result.score < 1.0


def test_repeated_punctuation():
    scorer = RegexScorer()
    result = scorer.score(_chunk("Fin de phrase....,,,,suite du texte"))
    assert result.value > 0


def test_empty_text():
    scorer = RegexScorer()
    result = scorer.score(_chunk(""))
    assert result.score == 1.0
    assert result.value == 0


def test_heavily_corrupted_text():
    """Heavily OCR-corrupted text should score very low."""
    scorer = RegexScorer()
    result = scorer.score(
        _chunk("L€$ c0nd!t!0n$ g€n€r@l€$ d€ v€nt€ $0nt @pp|!c@bl€$ @ t0ut€$ |€$ c0mm@nd€$.")
    )
    assert result.score < 0.5


# ── Custom patterns ─────────────────────────────────────────────────────


def test_custom_pattern_only():
    """Custom pattern without built-in."""
    scorer = RegexScorer(
        custom_patterns=[("zero_for_o", r"(?<=[a-z])0(?=[a-z])")],
        use_builtin=False,
    )
    result = scorer.score(_chunk("Les c0nditi0ns de vente"))
    assert result.value == 2  # c0nditi0ns has 2 matches
    assert result.score < 1.0


def test_custom_pattern_with_builtin():
    """Custom pattern added to built-in patterns."""
    scorer = RegexScorer(
        custom_patterns=[("exclamation_as_i", r"(?<=[a-z])!(?=[a-z])")],
    )
    result = scorer.score(_chunk("Les cond!t!ons sont appl!cables"))
    assert result.value > 0


def test_no_builtin():
    """With use_builtin=False and no custom, nothing is detected."""
    scorer = RegexScorer(use_builtin=False)
    result = scorer.score(_chunk("L€$ c0nd!t!0n$ g€n€r@l€$"))
    assert result.score == 1.0
    assert result.value == 0


def test_pattern_names():
    scorer = RegexScorer(custom_patterns=[("my_custom", r"xyz")])
    names = scorer.pattern_names
    builtin_names = [name for name, _, _ in BUILTIN_PATTERNS]
    assert all(n in names for n in builtin_names)
    assert "my_custom" in names


# ── Integration with validate_text ───────────────────────────────────────


def test_validate_text_with_custom_patterns():
    """custom_patterns flows through the public API."""
    from ocrval import validate_text

    result = validate_text(
        ["Les c0nditi0ns de vente s0nt applicables"],
        custom_patterns=[("zero_for_o", r"(?<=[a-z])0(?=[a-z])")],
    )
    assert "regex_artifacts" in result.chunk_scores[0].scores
    assert result.chunk_scores[0].scores["regex_artifacts"].value > 0
