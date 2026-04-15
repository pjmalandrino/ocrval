"""ocrval — OCR output quality validation."""

from ocrval.adapters.outbound.dictionary import FileDictionaryLoader, load_dictionary
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
    lang: str | None = None,
    custom_words: list[str] | None = None,
    good_threshold: float = 0.75,
    bad_threshold: float = 0.40,
) -> DocumentScoreResult:
    """Validate a Docling JSON document in one call.

    Args:
        docling_json: Raw Docling DoclingDocument dict.
        lang: Language code (e.g. "fr"). Downloads and caches the dictionary on first use.
        custom_words: Additional domain-specific words to include in the dictionary.
        good_threshold: Score above which a chunk is "good".
        bad_threshold: Score below which a chunk is "bad".

    Returns:
        DocumentScoreResult with overall score, bucket, per-chunk details, and flags.
    """
    adapter = DoclingAdapter()
    doc_id, chunks = adapter.extract(docling_json)
    return _run_validation(doc_id, chunks, lang, custom_words, good_threshold, bad_threshold)


def validate_text(
    texts: list[str],
    *,
    document_id: str = "document",
    lang: str | None = None,
    custom_words: list[str] | None = None,
    good_threshold: float = 0.75,
    bad_threshold: float = 0.40,
) -> DocumentScoreResult:
    """Validate a list of plain text chunks.

    Args:
        texts: List of text strings to validate.
        document_id: Optional document identifier.
        lang: Language code (e.g. "fr"). Downloads and caches the dictionary on first use.
        custom_words: Additional domain-specific words to include in the dictionary.
        good_threshold: Score above which a chunk is "good".
        bad_threshold: Score below which a chunk is "bad".

    Returns:
        DocumentScoreResult with overall score, bucket, per-chunk details, and flags.
    """
    adapter = GenericTextAdapter()
    doc_id, chunks = adapter.extract(texts, document_id=document_id)
    return _run_validation(doc_id, chunks, lang, custom_words, good_threshold, bad_threshold)


def _run_validation(
    doc_id: str,
    chunks: list[ChunkInput],
    lang: str | None,
    custom_words: list[str] | None,
    good_threshold: float,
    bad_threshold: float,
) -> DocumentScoreResult:
    dictionary = load_dictionary(lang=lang, custom_words=custom_words)

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
    "load_dictionary",
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
