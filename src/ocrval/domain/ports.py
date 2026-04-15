from typing import Any, Protocol

from ocrval.domain.models import ChunkInput, HeuristicResult


class Scorer(Protocol):
    """Port: a scoring heuristic that evaluates a single chunk.

    score values are normalized 0-1 where 1 = high quality.
    """

    name: str

    def score(self, chunk: ChunkInput) -> HeuristicResult: ...


class DocumentAdapter(Protocol):
    """Port: converts raw engine output into ChunkInputs.

    Implementations exist for Docling, plain text, and future engines.
    """

    def extract(self, raw: Any) -> tuple[str, list[ChunkInput]]:
        """Return (document_id, chunks) from raw engine output."""
        ...


class DictionaryPort(Protocol):
    """Port: provides a word set for dictionary-based scoring."""

    def load(self, path: str) -> set[str]: ...
