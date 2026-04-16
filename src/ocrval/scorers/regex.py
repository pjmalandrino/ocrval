"""Regex-based scorer — detects OCR artifacts via configurable patterns.

Built-in patterns catch common OCR failure modes. Custom patterns can be
added for domain-specific artifact detection (like the dictionary's custom_words).
"""

import re

from ocrval.domain.models import ChunkInput, HeuristicResult

# ── Built-in OCR artifact patterns ──────────────────────────────────────
#
# Each entry: (name, compiled_regex, description)
# A match indicates a likely OCR artifact. More matches → lower score.

BUILTIN_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "pipe_as_letter",
        re.compile(
            r"(?<=[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ])\|(?=[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ])"
        ),
        "Pipe character | used as l or I between letters",
    ),
    (
        "currency_as_letter",
        re.compile(r"(?<=[a-zA-Z])[€$£](?=[a-zA-Z])"),
        "Currency symbol used as letter substitute (e.g. € for e)",
    ),
    (
        "at_as_letter",
        re.compile(r"(?<=[a-zA-Z])@(?=[a-zA-Z])"),
        "@ used as letter substitute (e.g. @ for a)",
    ),
    (
        "digit_letter_mix",
        re.compile(r"(?<=[a-zA-Z])[0-9](?=[a-zA-Z]){2}|(?<=[a-zA-Z]){2}[0-9](?=[a-zA-Z])"),
        "Digit mixed into word (e.g. c0nditions, l3s)",
    ),
    (
        "garbage_sequence",
        re.compile(r"[^\w\s.,;:!?'\"\-/()\[\]]{3,}"),
        "3+ consecutive non-standard characters",
    ),
    (
        "repeated_punctuation",
        re.compile(r"[.,;:!?]{4,}"),
        "4+ repeated punctuation marks (OCR stutter)",
    ),
    (
        "broken_whitespace",
        re.compile(r"(?<=[a-zA-Z]) {3,}(?=[a-zA-Z])"),
        "Excessive whitespace between words (broken layout)",
    ),
]


class RegexScorer:
    """Detects OCR artifacts via regex pattern matching.

    Uses built-in patterns for common OCR failure modes, plus optional
    custom patterns for domain-specific detection.

    Score: 1.0 = no artifacts, 0.0 = heavily corrupted.
    The ``value`` field reports the total number of matches found.
    """

    name: str = "regex_artifacts"

    def __init__(
        self,
        *,
        custom_patterns: list[tuple[str, str]] | None = None,
        threshold: float = 0.10,
        use_builtin: bool = True,
    ) -> None:
        """
        Args:
            custom_patterns: List of (name, regex_string) tuples to add.
                Each regex should match an OCR artifact pattern.
                Example: ``[("zero_for_o", r"(?<=[a-z])0(?=[a-z])")]``
            threshold: Ratio of matches/chars above which score drops to 0.
                Default 0.10 (10% of characters matched by artifact patterns).
            use_builtin: Whether to include built-in OCR artifact patterns.
                Set to False to use only custom patterns.
        """
        self.threshold = threshold
        self._patterns: list[tuple[str, re.Pattern[str], str]] = []

        if use_builtin:
            self._patterns.extend(BUILTIN_PATTERNS)

        if custom_patterns:
            for pat_name, pat_str in custom_patterns:
                self._patterns.append((pat_name, re.compile(pat_str), f"Custom: {pat_name}"))

    @property
    def pattern_names(self) -> list[str]:
        """List of active pattern names."""
        return [name for name, _, _ in self._patterns]

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        text = chunk.text
        if not text or len(text) < 2:
            return HeuristicResult(value=0, score=1.0)

        total_matches = 0
        for _, pattern, _ in self._patterns:
            total_matches += len(pattern.findall(text))

        if total_matches == 0:
            return HeuristicResult(value=0, score=1.0)

        ratio = total_matches / len(text)
        score = max(0.0, 1.0 - (ratio / self.threshold))
        return HeuristicResult(value=total_matches, score=round(score, 4))
