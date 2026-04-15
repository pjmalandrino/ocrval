import logging
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)


class FileDictionaryLoader:
    """Loads a word list from a plain text file (one word per line)."""

    def load(self, path: str) -> set[str]:
        file = Path(path)
        if not file.exists():
            logger.warning("Dictionary file not found at %s — dictionary scorer disabled", path)
            return set()

        words: set[str] = set()
        with file.open(encoding="utf-8") as f:
            for line in f:
                word = line.strip().lower()
                if word and not word.startswith("#"):
                    word = word.split("/")[0]
                    word = unicodedata.normalize("NFC", word)
                    words.add(word)

        logger.info("Loaded %d words from %s", len(words), path)
        return words
