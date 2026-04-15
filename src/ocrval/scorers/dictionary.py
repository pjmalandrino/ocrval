import re
import unicodedata

from ocrval.domain.models import ChunkInput, HeuristicResult

_WORD_PATTERN = re.compile(r"[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ]+")


class DictionaryScorer:
    name: str = "dictionary_ratio"

    def __init__(self, dictionary: set[str], threshold: float = 0.30) -> None:
        self.dictionary = dictionary
        self.threshold = threshold

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        text = unicodedata.normalize("NFC", chunk.text)
        words = [w.lower() for w in _WORD_PATTERN.findall(text) if len(w) >= 2]

        if not words:
            return HeuristicResult(value=1.0, score=0.0)

        if not self.dictionary:
            return HeuristicResult(value=0.0, score=1.0)

        oov_count = sum(1 for w in words if w not in self.dictionary)
        ratio = oov_count / len(words)

        score = max(0.0, 1.0 - (ratio / self.threshold))
        return HeuristicResult(value=round(ratio, 4), score=round(score, 4))
