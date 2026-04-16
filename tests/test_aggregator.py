"""Tests for aggregator functions: aggregate_document, aggregate_chunk_split, generate_flags."""

from ocrval.domain.models import ChunkInput, ChunkResult, HeuristicResult
from ocrval.pipeline.aggregator import (
    aggregate_chunk_split,
    aggregate_document,
    generate_flags,
)


def _make_chunk_result(
    text: str,
    scores: dict[str, tuple[float, float]],
    page_no: int = 1,
) -> ChunkResult:
    """Helper: scores is {name: (value, score)}."""
    return ChunkResult(
        chunk=ChunkInput(ref="#/texts/0", label="paragraph", page_no=page_no, text=text),
        heuristics={name: HeuristicResult(value=v, score=s) for name, (v, s) in scores.items()},
    )


# --- aggregate_document ---


def test_aggregate_document_single_chunk():
    cr = _make_chunk_result("hello world", {"a": (0.1, 0.8)})
    score = aggregate_document([cr], {"a": 1.0})
    assert abs(score - 0.8) < 0.001


def test_aggregate_document_weighted_by_length():
    short = _make_chunk_result("hi", {"a": (0.1, 1.0)})  # len=2
    long = _make_chunk_result("a" * 100, {"a": (0.1, 0.0)})  # len=100
    # weighted: (1.0*2 + 0.0*100) / (2+100) = 2/102 ≈ 0.0196
    score = aggregate_document([short, long], {"a": 1.0})
    assert score < 0.05


def test_aggregate_document_empty():
    score = aggregate_document([], {"a": 1.0})
    assert score == 0.0


# --- aggregate_chunk_split ---


def test_chunk_split_quality_only():
    heuristics = {
        "special_char_ratio": HeuristicResult(value=0.1, score=0.9),
        "dictionary_ratio": HeuristicResult(value=0.8, score=0.8),
    }
    weights = {"special_char_ratio": 0.5, "dictionary_ratio": 0.5}
    quality, usability = aggregate_chunk_split(heuristics, weights)
    assert abs(quality - 0.85) < 0.001
    assert usability == 0.0  # no usability scorers present


def test_chunk_split_both_groups():
    heuristics = {
        "special_char_ratio": HeuristicResult(value=0.05, score=0.9),
        "dictionary_ratio": HeuristicResult(value=0.8, score=0.8),
        "short_chunk": HeuristicResult(value=False, score=1.0),
        "line_repetition": HeuristicResult(value=1, score=0.6),
    }
    weights = {
        "special_char_ratio": 0.25,
        "dictionary_ratio": 0.35,
        "short_chunk": 0.20,
        "line_repetition": 0.20,
    }
    quality, usability = aggregate_chunk_split(heuristics, weights)
    # quality = (0.9*0.25 + 0.8*0.35) / (0.25+0.35) = (0.225+0.28)/0.60 = 0.8417
    assert abs(quality - 0.8417) < 0.01
    # usability = (1.0*0.20 + 0.6*0.20) / (0.20+0.20) = (0.20+0.12)/0.40 = 0.80
    assert abs(usability - 0.80) < 0.01


# --- generate_flags ---


def test_generate_flags_short_chunks():
    cr = _make_chunk_result("OK", {"short_chunk": (True, 0.0)})
    flags = generate_flags([cr], {}, bad_threshold=0.40)
    assert any("short" in f.lower() for f in flags)


def test_generate_flags_repeated_lines():
    cr = _make_chunk_result("x\nx\nx", {"line_repetition": (3, 0.2)})
    flags = generate_flags([cr], {}, bad_threshold=0.40)
    assert any("repeated" in f.lower() for f in flags)


def test_generate_flags_special_char():
    cr = _make_chunk_result("$$$", {"special_char_ratio": (0.9, 0.1)}, page_no=5)
    flags = generate_flags([cr], {}, bad_threshold=0.40)
    assert any("page 5" in f for f in flags)


def test_generate_flags_no_issues():
    cr = _make_chunk_result(
        "good text",
        {
            "special_char_ratio": (0.01, 0.95),
            "dictionary_ratio": (0.9, 0.9),
            "short_chunk": (False, 1.0),
            "line_repetition": (1, 1.0),
        },
    )
    flags = generate_flags([cr], {}, bad_threshold=0.40)
    assert flags == []


def test_generate_flags_uses_threshold():
    cr = _make_chunk_result("text", {"special_char_ratio": (0.5, 0.35)}, page_no=1)
    # With default 0.40 threshold: 0.35 < 0.40 → flagged
    flags_strict = generate_flags([cr], {}, bad_threshold=0.40)
    assert len(flags_strict) == 1
    # With 0.30 threshold: 0.35 >= 0.30 → not flagged
    flags_lax = generate_flags([cr], {}, bad_threshold=0.30)
    assert len(flags_lax) == 0
