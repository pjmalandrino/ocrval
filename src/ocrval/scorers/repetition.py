from collections import Counter

from ocrval.domain.models import ChunkInput, HeuristicResult


class RepetitionScorer:
    """Detects repeated text chunks (common OCR artifact from headers/footers).

    Must be initialized with the full chunk list before scoring individual chunks.
    """

    name: str = "line_repetition"

    def __init__(self, min_occurrences: int = 3) -> None:
        self.min_occurrences = min_occurrences
        self._frequency: Counter[str] = Counter()

    def prepare(self, chunks: list[ChunkInput]) -> None:
        """Build frequency map from all chunks. Call before score()."""
        self._frequency = Counter(
            chunk.text.strip().lower() for chunk in chunks if chunk.text.strip()
        )

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        normalized = chunk.text.strip().lower()

        if not normalized:
            return HeuristicResult(value=0, score=1.0)

        count = self._frequency.get(normalized, 0)

        if count >= self.min_occurrences:
            return HeuristicResult(value=count, score=0.0)

        return HeuristicResult(value=count, score=1.0)
