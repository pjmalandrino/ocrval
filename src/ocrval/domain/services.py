from ocrval.domain.models import (
    Bucket,
    ChunkInput,
    ChunkScoreResult,
    DocumentScoreResult,
)
from ocrval.pipeline.aggregator import (
    aggregate_chunk,
    aggregate_chunk_split,
    aggregate_document,
    classify,
    generate_flags,
)
from ocrval.pipeline.registry import ScoringPipeline


class ValidationService:
    """Core service — orchestrates scoring pipeline on chunks."""

    def __init__(
        self,
        pipeline: ScoringPipeline,
        weights: dict[str, float],
        good_threshold: float = 0.75,
        bad_threshold: float = 0.40,
    ) -> None:
        self._pipeline = pipeline
        self._weights = weights
        self._good = good_threshold
        self._bad = bad_threshold

    def validate(self, document_id: str, chunks: list[ChunkInput]) -> DocumentScoreResult:
        if not chunks:
            return DocumentScoreResult(
                document_id=document_id,
                overall_score=0.0,
                bucket=Bucket.BAD,
                chunk_scores=[],
                flags=["No text chunks extracted from document"],
                scorer_versions={"scorers": []},
            )

        chunk_results = self._pipeline.run(chunks)

        chunk_responses: list[ChunkScoreResult] = []
        for cr in chunk_results:
            chunk_score = aggregate_chunk(cr.heuristics, self._weights)
            quality_score, usability_score = aggregate_chunk_split(cr.heuristics, self._weights)
            bucket = classify(chunk_score, self._good, self._bad)
            preview = cr.chunk.text[:80] + "..." if len(cr.chunk.text) > 80 else cr.chunk.text
            chunk_responses.append(
                ChunkScoreResult(
                    chunk_ref=cr.chunk.ref,
                    label=cr.chunk.label,
                    page_no=cr.chunk.page_no,
                    text_preview=preview,
                    text_full=cr.chunk.text,
                    scores=cr.heuristics,
                    quality_score=round(quality_score, 4),
                    usability_score=round(usability_score, 4),
                    chunk_score=round(chunk_score, 4),
                    bucket=bucket,
                )
            )

        overall_score = aggregate_document(chunk_results, self._weights)
        overall_bucket = classify(overall_score, self._good, self._bad)
        flags = generate_flags(chunk_results, self._weights, bad_threshold=self._bad)

        return DocumentScoreResult(
            document_id=document_id,
            overall_score=round(overall_score, 4),
            bucket=overall_bucket,
            chunk_scores=chunk_responses,
            flags=flags,
            scorer_versions={
                "scorers": self._pipeline.scorer_names,
            },
        )
