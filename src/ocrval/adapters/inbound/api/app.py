"""FastAPI application — only usable with the [api] extra installed."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ocrval.adapters.inbound.api.router import init_router, router
from ocrval.adapters.outbound.dictionary import load_dictionary
from ocrval.config import settings
from ocrval.domain.services import ValidationService
from ocrval.pipeline.registry import ScoringPipeline
from ocrval.scorers.dictionary import DictionaryScorer
from ocrval.scorers.regex import RegexScorer
from ocrval.scorers.repetition import RepetitionScorer
from ocrval.scorers.short_chunk import ShortChunkScorer
from ocrval.scorers.special_char import SpecialCharScorer


def _build_service(
    *,
    short_chunk_min_words: int | None = None,
) -> ValidationService:
    dictionary = load_dictionary(lang=settings.lang, custom_words=settings.custom_words)

    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer(threshold=settings.special_char_threshold))
    pipeline.register(
        DictionaryScorer(dictionary=dictionary, threshold=settings.dictionary_oov_threshold)
    )
    # Parse custom regex patterns from config: [["name", "regex"], ...]
    custom_patterns = None
    if settings.custom_regex_patterns:
        custom_patterns = [(p[0], p[1]) for p in settings.custom_regex_patterns if len(p) >= 2]

    pipeline.register(
        RegexScorer(
            custom_patterns=custom_patterns,
            threshold=settings.regex_artifact_threshold,
        )
    )
    pipeline.register(
        ShortChunkScorer(min_words=short_chunk_min_words or settings.short_chunk_min_words)
    )
    pipeline.register(RepetitionScorer(min_occurrences=settings.repetition_min_occurrences))

    weights = {
        "special_char_ratio": settings.weights.special_char_ratio,
        "dictionary_ratio": settings.weights.dictionary_ratio,
        "regex_artifacts": settings.weights.regex_artifacts,
        "short_chunk": settings.weights.short_chunk,
        "line_repetition": settings.weights.line_repetition,
    }

    return ValidationService(
        pipeline=pipeline,
        weights=weights,
        good_threshold=settings.bucket_good_threshold,
        bad_threshold=settings.bucket_bad_threshold,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = _build_service()
    init_router(service, build_service_fn=_build_service)
    yield


app = FastAPI(
    title="ocrval",
    version="0.1.0",
    description="OCR output quality validation API",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend static files if the directory exists (Docker build)
_static_dir = Path(os.environ.get("OCRVAL_STATIC_DIR", "/app/static"))
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
