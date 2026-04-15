from ocrval.adapters.outbound.docling import DoclingAdapter


def test_extract_texts(sample_docling_json):
    adapter = DoclingAdapter()
    doc_id, chunks = adapter.extract(sample_docling_json)
    assert doc_id == "test_document.pdf"
    assert len(chunks) == 4


def test_extract_table_text(sample_docling_json):
    adapter = DoclingAdapter()
    _, chunks = adapter.extract(sample_docling_json)
    table_chunk = [c for c in chunks if c.label == "table"][0]
    assert "Article" in table_chunk.text
    assert "1200" in table_chunk.text


def test_page_numbers(sample_docling_json):
    adapter = DoclingAdapter()
    _, chunks = adapter.extract(sample_docling_json)
    assert chunks[0].page_no == 1
    assert chunks[2].page_no == 2


def test_empty_json():
    adapter = DoclingAdapter()
    doc_id, chunks = adapter.extract({"name": "empty.pdf"})
    assert doc_id == "empty.pdf"
    assert len(chunks) == 0


def test_chunked_format():
    """Docling-serve chunking endpoint returns a 'chunks' key instead of 'texts'."""
    adapter = DoclingAdapter()
    raw = {
        "chunks": [
            {
                "text": "Premier paragraphe du document.",
                "block_type": None,
                "page_numbers": [1],
                "doc_items": ["#/texts/0", "#/texts/1"],
            },
            {
                "text": "| Col A | Col B |\n|-------|-------|\n| 1     | 2     |",
                "block_type": None,
                "page_numbers": [2],
                "doc_items": ["#/tables/0"],
            },
        ]
    }
    doc_id, chunks = adapter.extract(raw)
    assert doc_id == "unknown"
    assert len(chunks) == 2
    assert chunks[0].text == "Premier paragraphe du document."
    assert chunks[0].ref == "#/texts/0"
    assert chunks[0].page_no == 1
    assert chunks[1].page_no == 2
