"""Integration tests for the FastAPI endpoint."""

import pytest

try:
    from fastapi.testclient import TestClient

    from ocrval.adapters.inbound.api.app import app

    HAS_API = True
except ImportError:
    HAS_API = False

pytestmark = pytest.mark.skipif(not HAS_API, reason="fastapi not installed (needs [api] extra)")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_validate_basic(client, sample_docling_json):
    resp = client.post("/v1/validate", json=sample_docling_json)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
    assert "bucket" in data
    assert data["bucket"] in ("good", "uncertain", "bad")
    assert len(data["chunk_scores"]) > 0


def test_validate_returns_quality_usability(client, sample_docling_json):
    resp = client.post("/v1/validate", json=sample_docling_json)
    data = resp.json()
    for cs in data["chunk_scores"]:
        assert "quality_score" in cs
        assert "usability_score" in cs
        assert "chunk_score" in cs
        assert isinstance(cs["quality_score"], int | float)
        assert isinstance(cs["usability_score"], int | float)


def test_validate_with_short_chunk_override(client, sample_docling_json):
    resp = client.post("/v1/validate?short_chunk_min_words=10", json=sample_docling_json)
    assert resp.status_code == 200
    data = resp.json()
    # "Conditions" is one word, should be flagged with min_words=10
    short_flagged = any(
        cs["scores"].get("short_chunk", {}).get("value") is True for cs in data["chunk_scores"]
    )
    assert short_flagged


def test_validate_empty_texts(client):
    """Document with no texts/tables/chunks should return BAD with a flag."""
    resp = client.post("/v1/validate", json={"name": "empty.pdf", "texts": [], "tables": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bucket"] == "bad"
    assert any("no text" in f.lower() for f in data["flags"])


def test_validate_repetition_detected(client):
    """Regression test: repeated chunks should be detected via auto-prepare()."""
    doc = {
        "name": "repeated.pdf",
        "texts": [
            {
                "self_ref": f"#/texts/{i}",
                "label": "section_header",
                "text": "Page 1 sur 3",
                "prov": [{"page_no": i + 1}],
            }
            for i in range(5)
        ],
        "tables": [],
    }
    resp = client.post("/v1/validate", json=doc)
    assert resp.status_code == 200
    data = resp.json()
    # All chunks are identical → line_repetition should be < 1.0
    for cs in data["chunk_scores"]:
        rep_score = cs["scores"].get("line_repetition", {}).get("score", 1.0)
        assert rep_score < 1.0, f"Expected repetition detected, got score={rep_score}"
