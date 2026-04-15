from typing import Any

from fastapi import APIRouter, HTTPException

from ocrval.adapters.inbound.api.schemas import ChunkScoreResponse, DocumentScoreResponse
from ocrval.adapters.outbound.docling import DoclingAdapter
from ocrval.domain.models import Bucket

router = APIRouter(prefix="/v1")

# Injected at app startup
_validation_service = None


def init_router(validation_service):
    global _validation_service
    _validation_service = validation_service


@router.post("/validate", response_model=DocumentScoreResponse)
def validate_document(body: dict[str, Any]) -> DocumentScoreResponse:
    if _validation_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    adapter = DoclingAdapter()
    try:
        document_id, chunks = adapter.extract(body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid Docling JSON: {e}")

    result = _validation_service.validate(document_id, chunks)

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
                scores=cs.scores,
                chunk_score=cs.chunk_score,
                bucket=cs.bucket,
            )
            for cs in result.chunk_scores
        ],
        flags=result.flags,
        scorer_versions=result.scorer_versions,
    )
