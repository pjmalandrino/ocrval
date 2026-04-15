from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from ocrval.adapters.inbound.api.schemas import ChunkScoreResponse, DocumentScoreResponse
from ocrval.adapters.outbound.docling import DoclingAdapter
from ocrval.config import settings
from ocrval.domain.models import Bucket

router = APIRouter(prefix="/v1")

# Injected at app startup — used as default; rebuilt per-request when overrides are provided
_default_service = None
_build_service_fn = None


def init_router(validation_service, build_service_fn=None):
    global _default_service, _build_service_fn
    _default_service = validation_service
    _build_service_fn = build_service_fn


@router.post("/validate", response_model=DocumentScoreResponse)
def validate_document(
    body: dict[str, Any],
    short_chunk_min_words: Optional[int] = Query(None, ge=1, description="Min word count for short_chunk scorer"),
    pass2: Optional[bool] = Query(None, description="Enable perplexity scoring (requires [llm] extra)"),
) -> DocumentScoreResponse:
    if _default_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # If overrides provided, rebuild service; otherwise use default
    has_overrides = short_chunk_min_words is not None or pass2 is not None
    if has_overrides and _build_service_fn:
        try:
            service = _build_service_fn(
                short_chunk_min_words=short_chunk_min_words or settings.short_chunk_min_words,
                pass2_enabled=pass2,
            )
        except ImportError as e:
            raise HTTPException(status_code=422, detail=str(e))
    else:
        service = _default_service

    adapter = DoclingAdapter()
    try:
        document_id, chunks = adapter.extract(body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid Docling JSON: {e}")

    result = service.validate(document_id, chunks)

    return DocumentScoreResponse(
        document_id=result.document_id,
        overall_score=result.overall_score,
        bucket=result.bucket,
        chunk_scores=[
            ChunkScoreResponse(
                chunk_ref=cs.chunk_ref,
                label=cs.label,
                page_no=cs.page_no,
                text_preview=cs.text_preview,
                text_full=cs.text_full,
                scores=cs.scores,
                chunk_score=cs.chunk_score,
                bucket=cs.bucket,
            )
            for cs in result.chunk_scores
        ],
        flags=result.flags,
        scorer_versions=result.scorer_versions,
    )
