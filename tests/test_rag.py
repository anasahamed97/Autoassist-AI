import pytest
from pathlib import Path
from backend.app.rag.text_cleaner import TextCleaner
from backend.app.rag.chunker import AutomotiveChunker
from backend.app.rag.document_loader import DocumentLoader
from backend.app.rag.embeddings import get_embedding_model


def test_text_cleaner():
    raw = "Section 1: Brakes\n\n\nPage 4 of 12\n\n  Replace brake pads.  \r\nCheck rotor.  "
    cleaned = TextCleaner.clean(raw)
    assert "Page 4 of 12" not in cleaned
    assert "Replace brake pads." in cleaned
    assert "\r" not in cleaned

    title = TextCleaner.extract_section_title("### SECTION 2: COOLING SYSTEM")
    assert title == "SECTION 2: COOLING SYSTEM"


def test_chunker():
    chunker = AutomotiveChunker(chunk_size=200, chunk_overlap=30)
    blocks = [
        {
            "text": (
                "## COOLING SYSTEM\n\n"
                "Engine overheating can be caused by low coolant level, stuck thermostat, "
                "or failing water pump. Always check for external leaks before opening the radiator cap.\n\n"
                "Electric cooling fans should activate when engine coolant temperature exceeds 205 degrees Fahrenheit. "
                "Inspect the fan relay and fuse if fans fail to rotate."
            ),
            "page_number": 1,
            "section": "COOLING SYSTEM",
        }
    ]
    chunks = chunker.chunk_text_blocks(blocks, document_id="doc-123")
    assert len(chunks) >= 1
    for c in chunks:
        assert c.document_id == "doc-123"
        assert c.page_number == 1
        assert len(c.content) > 0


def test_document_loader_md():
    p = Path("data/raw/cooling_system_service_manual.md")
    assert p.exists()
    doc = DocumentLoader.load_document(p)
    assert doc["content_hash"]
    assert len(doc["blocks"]) >= 3
    assert doc["metadata"].title


def test_document_loader_pdf():
    p = Path("data/raw/honda_civic_service_and_maintenance.pdf")
    assert p.exists()
    doc = DocumentLoader.load_document(p)
    assert doc["content_hash"]
    assert len(doc["blocks"]) == 4  # 4 pages
    assert any("HONDA CIVIC" in b["text"] for b in doc["blocks"])


def test_local_embeddings():
    model = get_embedding_model()
    vec = model.embed_query("What can cause an engine to overheat?")
    assert len(vec) == 384
    norm = sum(x**2 for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-4
