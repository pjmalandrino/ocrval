from ocrval.domain.models import ChunkInput


class GenericTextAdapter:
    """Converts a list of plain text strings into ChunkInputs.

    Use this when you don't have structured OCR output — just raw text chunks.
    """

    def extract(
        self, texts: list[str], document_id: str = "document"
    ) -> tuple[str, list[ChunkInput]]:
        chunks = [
            ChunkInput(ref=f"#/texts/{i}", label="paragraph", text=text)
            for i, text in enumerate(texts)
        ]
        return document_id, chunks
