from ocrval import validate_document, validate_text


def test_validate_document(sample_docling_json):
    result = validate_document(sample_docling_json)
    assert 0 <= result.overall_score <= 1
    assert result.bucket in ("good", "uncertain", "bad")
    assert len(result.chunk_scores) == 4


def test_validate_text():
    result = validate_text(["Bonjour le monde", ""])
    assert len(result.chunk_scores) == 2
    assert result.chunk_scores[1].bucket == "bad"


def test_validate_empty_document():
    result = validate_document({"name": "empty.pdf"})
    assert result.bucket == "bad"
    assert result.overall_score == 0.0
