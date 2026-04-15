from typing import Any

from ocrval.domain.models import ChunkInput


class DoclingAdapter:
    """Converts Docling JSON (DoclingDocument or chunking response) into ChunkInputs."""

    def extract(self, raw: dict[str, Any]) -> tuple[str, list[ChunkInput]]:
        # Auto-detect format: chunking response vs DoclingDocument
        if "chunks" in raw and "texts" not in raw:
            return self._extract_chunked(raw)
        return self._extract_document(raw)

    def _extract_chunked(self, raw: dict[str, Any]) -> tuple[str, list[ChunkInput]]:
        """Extract from docling-serve chunking endpoint response (key: 'chunks')."""
        document_id = raw.get("name", "unknown")
        chunks: list[ChunkInput] = []

        for i, item in enumerate(raw.get("chunks", [])):
            text = item.get("text", "")

            # Use first doc_items ref or generate one
            doc_items = item.get("doc_items", [])
            ref = doc_items[0] if doc_items else f"#/chunks/{i}"

            label = item.get("block_type") or "chunk"

            page_no = None
            page_numbers = item.get("page_numbers", [])
            if page_numbers:
                page_no = page_numbers[0]

            chunks.append(ChunkInput(ref=ref, label=label, page_no=page_no, text=text))

        return document_id, chunks

    def _extract_document(self, raw: dict[str, Any]) -> tuple[str, list[ChunkInput]]:
        """Extract from DoclingDocument format (keys: 'texts', 'tables')."""
        document_id = raw.get("name", "unknown")
        chunks: list[ChunkInput] = []

        for item in raw.get("texts", []):
            text = item.get("text", "")
            ref = item.get("self_ref", f"#/texts/{len(chunks)}")
            label = item.get("label", "unknown")

            page_no = None
            prov = item.get("prov", [])
            if prov:
                page_no = prov[0].get("page_no")

            chunks.append(ChunkInput(ref=ref, label=label, page_no=page_no, text=text))

        for table in raw.get("tables", []):
            ref = table.get("self_ref", f"#/tables/{len(chunks)}")
            label = table.get("label", "table")

            page_no = None
            prov = table.get("prov", [])
            if prov:
                page_no = prov[0].get("page_no")

            cell_texts: list[str] = []
            data = table.get("data", {})
            for row in data.get("grid", []):
                for cell in row:
                    cell_text = cell.get("text", "") if isinstance(cell, dict) else ""
                    if cell_text:
                        cell_texts.append(cell_text)

            chunks.append(
                ChunkInput(ref=ref, label=label, page_no=page_no, text=" ".join(cell_texts))
            )

        return document_id, chunks
