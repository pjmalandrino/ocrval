"""ocrval — OCR output quality validation."""

from ocrval.adapters.outbound.dictionary import FileDictionaryLoader
from ocrval.adapters.outbound.docling import DoclingAdapter
from ocrval.adapters.outbound.generic import GenericTextAdapter
from ocrval.domain.models import Bucket, ChunkInput, DocumentScoreResult, HeuristicResult
from ocrval.domain.services import ValidationService
from ocrval.pipeline.registry import ScoringPipeline
from ocrval.scorers.dictionary import DictionaryScorer
from ocrval.scorers.repetition import RepetitionScorer
from ocrval.scorers.short_chunk import ShortChunkScorer
from ocrval.scorers.special_char import SpecialCharScorer

__version__ = "0.1.0"


def validate_document(
    docling_json: dict,
    *,
    dictionary_path: str | None = None,
    good_threshold: float = 0.75,
    bad_threshold: float = 0.40,
) -> DocumentScoreResult:
    """Validate a Docling JSON document in one call.

    Args:
        docling_json: Raw Docling DoclingDocument dict.
        dictionary_path: Path to a word list file (one word per line).
        good_threshold: Score above which a chunk is "good".
        bad_threshold: Score below which a chunk is "bad".

    Returns:
        DocumentScoreResult with overall score, bucket, per-chunk details, and flags.
    """
    adapter = DoclingAdapter()
    doc_id, chunks = adapter.extract(docling_json)
    return _run_validation(doc_id, chunks, dictionary_path, good_threshold, bad_threshold)


def validate_text(
    texts: list[str],
    *,
    document_id: str = "document",
    dictionary_path: str | None = None,
    good_threshold: float = 0.75,
    bad_threshold: float = 0.40,
) -> DocumentScoreResult:
    """Validate a list of plain text chunks.

    Args:
        texts: List of text strings to validate.
        document_id: Optional document identifier.
        dictionary_path: Path to a word list file (one word per line).
        good_threshold: Score above which a chunk is "good".
        bad_threshold: Score below which a chunk is "bad".

    Returns:
        DocumentScoreResult with overall score, bucket, per-chunk details, and flags.
    """
    adapter = GenericTextAdapter()
    doc_id, chunks = adapter.extract(texts, document_id=document_id)
    return _run_validation(doc_id, chunks, dictionary_path, good_threshold, bad_threshold)


def _run_validation(
    doc_id: str,
    chunks: list[ChunkInput],
    dictionary_path: str | None,
    good_threshold: float,
    bad_threshold: float,
) -> DocumentScoreResult:
    dictionary: set[str] = set()
    if dictionary_path:
        dictionary = FileDictionaryLoader().load(dictionary_path)

    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer())
    pipeline.register(DictionaryScorer(dictionary=dictionary))
    pipeline.register(ShortChunkScorer())

    repetition_scorer = RepetitionScorer()
    repetition_scorer.prepare(chunks)
    pipeline.register(repetition_scorer)

    weights = {
        "special_char_ratio": 0.25,
        "dictionary_ratio": 0.35,
        "short_chunk": 0.20,
        "line_repetition": 0.20,
    }

    service = ValidationService(
        pipeline=pipeline,
        weights=weights,
        good_threshold=good_threshold,
        bad_threshold=bad_threshold,
    )
    return service.validate(doc_id, chunks)


__all__ = [
    "__version__",
    "validate_document",
    "validate_text",
    "Bucket",
    "ChunkInput",
    "DocumentScoreResult",
    "HeuristicResult",
    "ValidationService",
    "ScoringPipeline",
    "DoclingAdapter",
    "GenericTextAdapter",
    "FileDictionaryLoader",
    "SpecialCharScorer",
    "DictionaryScorer",
    "ShortChunkScorer",
    "RepetitionScorer",
]
