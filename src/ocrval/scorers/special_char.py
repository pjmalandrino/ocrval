import re

from ocrval.domain.models import ChunkInput, HeuristicResult

# Normal characters: letters, digits, whitespace, standard French punctuation
_NORMAL_PATTERN = re.compile(
    r"[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ0-9\s.,;:!?'\"\-/() ]"
)
_ALPHA_PATTERN = re.compile(r"[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ]")


class SpecialCharScorer:
    name: str = "special_char_ratio"

    def __init__(self, threshold: float = 0.15) -> None:
        self.threshold = threshold

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        text = chunk.text
        if not text:
            return HeuristicResult(value=0.0, score=0.0)

        alpha_count = len(_ALPHA_PATTERN.findall(text))
        if alpha_count == 0:
            return HeuristicResult(value=1.0, score=0.0)

        special_count = len(_NORMAL_PATTERN.sub("", text))
        ratio = special_count / alpha_count

        score = max(0.0, 1.0 - (ratio / self.threshold))
        return HeuristicResult(value=round(ratio, 4), score=round(score, 4))
