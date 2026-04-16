"""ocrval — OCR output quality validation."""

from ocrval.adapters.outbound.dictionary import FileDictionaryLoader, load_dictionary
from ocrval.adapters.outbound.docling import DoclingAdapter
from ocrval.adapters.outbound.generic import GenericTextAdapter
from ocrval.domain.models import Bucket, ChunkInput, DocumentScoreResult, HeuristicResult
from ocrval.domain.services import ValidationService
from ocrval.pipeline.registry import ScoringPipeline
from ocrval.scorers.dictionary import DictionaryScorer
from ocrval.scorers.regex import RegexScorer
from ocrval.scorers.repetition import RepetitionScorer
from ocrval.scorers.short_chunk import ShortChunkScorer
from ocrval.scorers.special_char import SpecialCharScorer

__version__ = "0.1.0"


def validate_document(
    docling_json: dict,
    *,
    lang: str | None = None,
    custom_words: list[str] | None = None,
    custom_patterns: list[tuple[str, str]] | None = None,
    good_threshold: float = 0.75,
    bad_threshold: float = 0.40,
    short_chunk_min_words: int = 3,
) -> DocumentScoreResult:
    """Validate a Docling JSON document in one call.

    Args:
        docling_json: Raw Docling DoclingDocument dict.
        lang: Language code (e.g. "fr"). Downloads and caches the dictionary on first use.
        custom_words: Additional domain-specific words to include in the dictionary.
        custom_patterns: Additional regex patterns for artifact detection.
            Each entry is a ``(name, regex_string)`` tuple.
            Example: ``[("zero_for_o", r"(?<=[a-z])0(?=[a-z])")]``
        good_threshold: Score above which a chunk is "good".
        bad_threshold: Score below which a chunk is "bad".
        short_chunk_min_words: Minimum word count before a chunk is flagged as short.

    Returns:
        DocumentScoreResult with overall score, bucket, per-chunk details, and flags.
    """
    adapter = DoclingAdapter()
    doc_id, chunks = adapter.extract(docling_json)
    return _run_validation(
        doc_id,
        chunks,
        lang,
        custom_words,
        custom_patterns,
        good_threshold,
        bad_threshold,
        short_chunk_min_words,
    )


def validate_text(
    texts: list[str],
    *,
    document_id: str = "document",
    lang: str | None = None,
    custom_words: list[str] | None = None,
    custom_patterns: list[tuple[str, str]] | None = None,
    good_threshold: float = 0.75,
    bad_threshold: float = 0.40,
    short_chunk_min_words: int = 3,
) -> DocumentScoreResult:
    """Validate a list of plain text chunks.

    Args:
        texts: List of text strings to validate.
        document_id: Optional document identifier.
        lang: Language code (e.g. "fr"). Downloads and caches the dictionary on first use.
        custom_words: Additional domain-specific words to include in the dictionary.
        custom_patterns: Additional regex patterns for artifact detection.
            Each entry is a ``(name, regex_string)`` tuple.
        good_threshold: Score above which a chunk is "good".
        bad_threshold: Score below which a chunk is "bad".
        short_chunk_min_words: Minimum word count before a chunk is flagged as short.

    Returns:
        DocumentScoreResult with overall score, bucket, per-chunk details, and flags.
    """
    adapter = GenericTextAdapter()
    doc_id, chunks = adapter.extract(texts, document_id=document_id)
    return _run_validation(
        doc_id,
        chunks,
        lang,
        custom_words,
        custom_patterns,
        good_threshold,
        bad_threshold,
        short_chunk_min_words,
    )


def _run_validation(
    doc_id: str,
    chunks: list[ChunkInput],
    lang: str | None,
    custom_words: list[str] | None,
    custom_patterns: list[tuple[str, str]] | None,
    good_threshold: float,
    bad_threshold: float,
    short_chunk_min_words: int = 3,
) -> DocumentScoreResult:
    dictionary = load_dictionary(lang=lang, custom_words=custom_words)

    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer())
    pipeline.register(DictionaryScorer(dictionary=dictionary))
    pipeline.register(RegexScorer(custom_patterns=custom_patterns))
    pipeline.register(ShortChunkScorer(min_words=short_chunk_min_words))
    pipeline.register(RepetitionScorer())

    weights = {
        "special_char_ratio": 0.20,
        "dictionary_ratio": 0.30,
        "regex_artifacts": 0.15,
        "short_chunk": 0.15,
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
    "Bucket",
    "ChunkInput",
    "DictionaryScorer",
    "DoclingAdapter",
    "DocumentScoreResult",
    "FileDictionaryLoader",
    "GenericTextAdapter",
    "HeuristicResult",
    "RegexScorer",
    "RepetitionScorer",
    "ScoringPipeline",
    "ShortChunkScorer",
    "SpecialCharScorer",
    "ValidationService",
    "__version__",
    "load_dictionary",
    "validate_document",
    "validate_text",
]
