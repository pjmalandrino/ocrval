from ocrval.domain.models import ChunkInput, HeuristicResult


class ShortChunkScorer:
    name: str = "short_chunk"

    def __init__(self, min_words: int = 3) -> None:
        self.min_words = min_words

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        text = chunk.text.strip()

        if not text:
            return HeuristicResult(value=True, score=0.0)

        word_count = len(text.split())
        if word_count < self.min_words:
            return HeuristicResult(value=True, score=0.3)

        return HeuristicResult(value=False, score=1.0)
