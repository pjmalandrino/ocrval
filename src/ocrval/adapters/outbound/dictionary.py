import logging
import unicodedata
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".cache" / "ocrval" / "dictionaries"

# Registry of known language wordlists
_LANGUAGE_SOURCES: dict[str, str] = {
    "fr": "https://raw.githubusercontent.com/chrplr/openlexicon/master/datasets-info/Liste-de-mots-francais-Gutenberg/liste.de.mots.francais.frgut.txt",
}


def _download_wordlist(lang: str) -> Path:
    """Download a wordlist for the given language and cache it locally."""
    if lang not in _LANGUAGE_SOURCES:
        supported = ", ".join(sorted(_LANGUAGE_SOURCES.keys()))
        raise ValueError(f"Unsupported language '{lang}'. Supported: {supported}")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{lang}.txt"

    if cache_file.exists():
        logger.debug("Using cached wordlist for '%s' at %s", lang, cache_file)
        return cache_file

    url = _LANGUAGE_SOURCES[lang]
    logger.info("Downloading '%s' wordlist from %s ...", lang, url)
    urllib.request.urlretrieve(url, cache_file)
    logger.info("Cached wordlist at %s", cache_file)
    return cache_file


class FileDictionaryLoader:
    """Loads a word list from a plain text file (one word per line)."""

    def load(self, path: str) -> set[str]:
        file = Path(path)
        if not file.exists():
            logger.warning("Dictionary file not found at %s — dictionary scorer disabled", path)
            return set()
        return _parse_wordlist(file)


def load_dictionary(
    lang: str | None = None,
    custom_words: list[str] | None = None,
) -> set[str]:
    """Load a dictionary by language code, with optional custom words.

    Args:
        lang: Language code (e.g. "fr"). Downloads and caches the wordlist on first use.
        custom_words: Additional words to include (domain-specific terms).

    Returns:
        Set of lowercase, NFC-normalized words.
    """
    words: set[str] = set()

    if lang:
        cache_file = _download_wordlist(lang)
        words = _parse_wordlist(cache_file)

    if custom_words:
        words.update(unicodedata.normalize("NFC", w.strip().lower()) for w in custom_words if w.strip())

    return words


def _parse_wordlist(path: Path) -> set[str]:
    """Parse a plain-text wordlist file into a normalized set."""
    words: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word and not word.startswith("#"):
                word = word.split("/")[0]
                word = unicodedata.normalize("NFC", word)
                words.add(word)
    logger.info("Loaded %d words from %s", len(words), path)
    return words
