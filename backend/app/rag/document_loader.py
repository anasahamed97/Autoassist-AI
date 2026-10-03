import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import pypdf

from backend.app.schemas.rag import DocumentMetadata
from backend.app.rag.text_cleaner import TextCleaner


class DocumentLoader:
    """
    Extracts text, metadata, page numbers, and sections from automotive service manuals
    in PDF, Markdown, or plain text formats.
    """

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Computes SHA-256 hash of file content for idempotent deduplication."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def load_document(
        cls,
        file_path: Path,
        override_metadata: Optional[DocumentMetadata] = None,
    ) -> Dict[str, Any]:
        """
        Loads and parses a document, returning:
        {
            'metadata': DocumentMetadata,
            'content_hash': str,
            'blocks': [{'text': str, 'page_number': int, 'section': str}, ...]
        }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content_hash = cls.calculate_file_hash(file_path)
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            blocks, extracted_meta = cls._load_pdf(file_path)
        elif suffix in [".md", ".txt"]:
            blocks, extracted_meta = cls._load_text(file_path)
        else:
            raise ValueError(f"Unsupported document format: {suffix}")

        # Merge metadata: user/manifest overrides take precedence
        meta_dict = extracted_meta.model_dump()
        if override_metadata:
            for k, v in override_metadata.model_dump().items():
                if v is not None:
                    meta_dict[k] = v

        final_metadata = DocumentMetadata(**meta_dict)

        return {
            "metadata": final_metadata,
            "content_hash": content_hash,
            "blocks": blocks,
            "file_path": str(file_path),
        }

    @staticmethod
    def _load_pdf(file_path: Path) -> tuple[List[Dict[str, Any]], DocumentMetadata]:
        reader = pypdf.PdfReader(str(file_path))
        blocks: List[Dict[str, Any]] = []

        title = file_path.stem.replace("_", " ").title()
        doc_info = reader.metadata
        if doc_info:
            pdf_title = getattr(doc_info, "title", None) or (doc_info.get("/Title") if isinstance(doc_info, dict) else None)
            if pdf_title:
                title = str(pdf_title)

        metadata = DocumentMetadata(
            title=title,
            source=file_path.name,
            document_type="Service Manual",
        )

        for page_idx, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            cleaned = TextCleaner.clean(raw_text)
            if not cleaned:
                continue

            section = TextCleaner.extract_section_title(cleaned)
            blocks.append({
                "text": cleaned,
                "page_number": page_idx + 1,
                "section": section,
            })

        return blocks, metadata

    @staticmethod
    def _load_text(file_path: Path) -> tuple[List[Dict[str, Any]], DocumentMetadata]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        title = file_path.stem.replace("_", " ").title()
        metadata = DocumentMetadata(
            title=title,
            source=file_path.name,
            document_type="Technical Diagnostic Guide",
        )

        blocks: List[Dict[str, Any]] = []
        # Check if form feed or page comments exist
        if "\f" in content:
            raw_pages = content.split("\f")
        elif "<!-- PAGE " in content:
            import re
            raw_pages = re.split(r"<!--\s*PAGE\s+\d+\s*-->", content)
        else:
            raw_pages = [content]

        for p_idx, p_text in enumerate(raw_pages):
            cleaned = TextCleaner.clean(p_text)
            if not cleaned:
                continue
            section = TextCleaner.extract_section_title(cleaned)
            blocks.append({
                "text": cleaned,
                "page_number": p_idx + 1,
                "section": section,
            })

        return blocks, metadata
