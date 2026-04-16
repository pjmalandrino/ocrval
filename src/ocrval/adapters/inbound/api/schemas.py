from typing import Any

from pydantic import BaseModel

from ocrval.domain.models import Bucket, HeuristicResult


class ChunkScoreResponse(BaseModel):
    chunk_ref: str
    label: str
    page_no: int | None = None
    text_preview: str
    text_full: str = ""
    scores: dict[str, HeuristicResult]
    quality_score: float = 0.0
    usability_score: float = 0.0
    chunk_score: float
    bucket: Bucket


class DocumentScoreResponse(BaseModel):
    document_id: str
    overall_score: float
    bucket: Bucket
    chunk_scores: list[ChunkScoreResponse]
    flags: list[str]
    scorer_versions: dict[str, Any]
