from typing import Any

from ocrval.domain.models import ChunkInput


class DoclingAdapter:
    """Converts Docling JSON (DoclingDocument) into ChunkInputs."""

    def extract(self, raw: dict[str, Any]) -> tuple[str, list[ChunkInput]]:
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
