import pytest

from ocrval.domain.models import ChunkInput


@pytest.fixture
def good_chunk() -> ChunkInput:
    return ChunkInput(
        ref="#/texts/0",
        label="paragraph",
        page_no=1,
        text="Le montant total de la facture est de mille deux cents euros.",
    )


@pytest.fixture
def bad_chunk() -> ChunkInput:
    return ChunkInput(
        ref="#/texts/1",
        label="paragraph",
        page_no=2,
        text="L€$ c0nd!t!0n$ g€n€r@l€$ d€ v€nt€ $0nt @pp|!c@bl€$ @ t0ut€$ |€$ c0mm@nd€$.",
    )


@pytest.fixture
def empty_chunk() -> ChunkInput:
    return ChunkInput(ref="#/texts/2", label="paragraph", page_no=3, text="")


@pytest.fixture
def short_chunk() -> ChunkInput:
    return ChunkInput(ref="#/texts/3", label="paragraph", page_no=1, text="OK")


@pytest.fixture
def fr_dictionary() -> set[str]:
    return {
        "le",
        "la",
        "les",
        "de",
        "des",
        "du",
        "un",
        "une",
        "est",
        "et",
        "en",
        "que",
        "qui",
        "dans",
        "pour",
        "pas",
        "au",
        "ce",
        "il",
        "elle",
        "nous",
        "vous",
        "ils",
        "elles",
        "montant",
        "total",
        "facture",
        "mille",
        "deux",
        "cents",
        "euros",
        "bonjour",
        "merci",
        "avec",
        "sur",
        "par",
        "son",
        "ses",
    }


@pytest.fixture
def sample_docling_json() -> dict:
    return {
        "name": "test_document.pdf",
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "paragraph",
                "text": "Le montant total de la facture est de mille deux cents euros.",
                "prov": [{"page_no": 1}],
            },
            {
                "self_ref": "#/texts/1",
                "label": "section_header",
                "text": "Conditions",
                "prov": [{"page_no": 1}],
            },
            {
                "self_ref": "#/texts/2",
                "label": "paragraph",
                "text": "Le montant total de la facture est conforme au devis initial.",
                "prov": [{"page_no": 2}],
            },
        ],
        "tables": [
            {
                "self_ref": "#/tables/0",
                "label": "table",
                "prov": [{"page_no": 1}],
                "data": {
                    "grid": [
                        [{"text": "Article"}, {"text": "Prix"}],
                        [{"text": "Service A"}, {"text": "1200"}],
                    ]
                },
            }
        ],
    }
