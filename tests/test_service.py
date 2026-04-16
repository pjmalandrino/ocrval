"""Tests for ValidationService: auto-prepare, quality/usability scores."""

from ocrval.domain.models import Bucket, ChunkInput
from ocrval.domain.services import ValidationService
from ocrval.pipeline.registry import ScoringPipeline
from ocrval.scorers.repetition import RepetitionScorer
from ocrval.scorers.short_chunk import ShortChunkScorer
from ocrval.scorers.special_char import SpecialCharScorer


def _make_chunks() -> list[ChunkInput]:
    return [
        ChunkInput(
            ref="#/texts/0",
            label="paragraph",
            page_no=1,
            text="Le montant total de la facture est de mille deux cents euros.",
        ),
        ChunkInput(ref="#/texts/1", label="section_header", page_no=1, text="Page 1 sur 3"),
        ChunkInput(ref="#/texts/2", label="section_header", page_no=2, text="Page 1 sur 3"),
        ChunkInput(ref="#/texts/3", label="section_header", page_no=3, text="Page 1 sur 3"),
    ]


def test_prepare_called_automatically():
    """Regression: RepetitionScorer.prepare() must be called by the pipeline."""
    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer())
    pipeline.register(ShortChunkScorer())
    pipeline.register(RepetitionScorer())

    service = ValidationService(
        pipeline=pipeline,
        weights={"special_char_ratio": 0.25, "short_chunk": 0.25, "line_repetition": 0.50},
    )

    chunks = _make_chunks()
    result = service.validate("test-doc", chunks)

    # The 3 repeated "Page 1 sur 3" chunks should have line_repetition < 1.0
    repeated_scores = [
        cs.scores["line_repetition"].score
        for cs in result.chunk_scores
        if cs.chunk_ref in ("#/texts/1", "#/texts/2", "#/texts/3")
    ]
    assert all(s < 1.0 for s in repeated_scores), f"Expected < 1.0, got {repeated_scores}"


def test_quality_usability_scores_populated():
    """quality_score and usability_score should be populated in chunk results."""
    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer())
    pipeline.register(ShortChunkScorer())
    pipeline.register(RepetitionScorer())

    service = ValidationService(
        pipeline=pipeline,
        weights={
            "special_char_ratio": 0.25,
            "short_chunk": 0.20,
            "line_repetition": 0.20,
        },
    )

    chunks = [
        ChunkInput(
            ref="#/texts/0",
            label="paragraph",
            page_no=1,
            text="Le montant total de la facture est de mille deux cents euros.",
        )
    ]
    result = service.validate("test-doc", chunks)

    cs = result.chunk_scores[0]
    # quality_score should be based on special_char_ratio only (only quality scorer present)
    assert cs.quality_score > 0
    # usability_score based on short_chunk + line_repetition
    assert cs.usability_score > 0
    # chunk_score combines all
    assert cs.chunk_score > 0


def test_empty_document():
    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer())

    service = ValidationService(pipeline=pipeline, weights={"special_char_ratio": 1.0})
    result = service.validate("empty-doc", [])

    assert result.overall_score == 0.0
    assert result.bucket == Bucket.BAD
    assert len(result.chunk_scores) == 0
    assert any("no text" in f.lower() for f in result.flags)
