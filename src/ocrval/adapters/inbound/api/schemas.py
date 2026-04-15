from typing import Any, Optional

from pydantic import BaseModel

from ocrval.domain.models import Bucket, HeuristicResult


class ChunkScoreResponse(BaseModel):
    chunk_ref: str
    label: str
    page_no: Optional[int] = None
    text_preview: str
    scores: dict[str, HeuristicResult]
    chunk_score: float
    bucket: Bucket


class DocumentScoreResponse(BaseModel):
    document_id: str
    overall_score: float
    bucket: Bucket
    chunk_scores: list[ChunkScoreResponse]
    flags: list[str]
    scorer_versions: dict[str, Any]
