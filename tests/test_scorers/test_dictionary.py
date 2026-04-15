from ocrval.domain.models import ChunkInput
from ocrval.scorers.dictionary import DictionaryScorer


def test_all_in_dictionary(good_chunk, fr_dictionary):
    scorer = DictionaryScorer(dictionary=fr_dictionary, threshold=0.30)
    result = scorer.score(good_chunk)
    assert result.score > 0.5


def test_gibberish(fr_dictionary):
    chunk = ChunkInput(ref="#/x", label="p", text="xkcd zqwrt bflmp nkrst")
    scorer = DictionaryScorer(dictionary=fr_dictionary, threshold=0.30)
    result = scorer.score(chunk)
    assert result.score == 0.0
    assert result.value == 1.0


def test_empty_dictionary():
    chunk = ChunkInput(ref="#/x", label="p", text="bonjour le monde")
    scorer = DictionaryScorer(dictionary=set(), threshold=0.30)
    result = scorer.score(chunk)
    assert result.score == 1.0


def test_empty_text(empty_chunk, fr_dictionary):
    scorer = DictionaryScorer(dictionary=fr_dictionary, threshold=0.30)
    result = scorer.score(empty_chunk)
    assert result.score == 0.0
