from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Bucket(str, Enum):
    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"


class ChunkInput(BaseModel):
    """A text chunk to validate — engine-agnostic."""

    ref: str
    label: str
    page_no: Optional[int] = None
    text: str


class HeuristicResult(BaseModel):
    """Result from a single scorer on a single chunk."""

    value: Any
    score: float


class ChunkResult(BaseModel):
    """All heuristic results for a single chunk."""

    chunk: ChunkInput
    heuristics: dict[str, HeuristicResult]


class ChunkScoreResult(BaseModel):
    """Aggregated score for a single chunk."""

    chunk_ref: str
    label: str
    page_no: Optional[int] = None
    text_preview: str
    text_full: str = ""
    scores: dict[str, HeuristicResult]
    chunk_score: float
    bucket: Bucket


class DocumentScoreResult(BaseModel):
    """Full validation result for a document."""

    document_id: str
    overall_score: float
    bucket: Bucket
    chunk_scores: list[ChunkScoreResult]
    flags: list[str]
    scorer_versions: dict[str, Any]
