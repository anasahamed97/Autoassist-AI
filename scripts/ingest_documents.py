"""
AutoAssist AI - Document Ingestion CLI Script
Ingests automotive service manuals, generates 384-dim embeddings,
and stores document metadata and chunks into Supabase PostgreSQL + pgvector.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.rag.document_loader import DocumentLoader
from backend.app.rag.chunker import AutomotiveChunker
from backend.app.rag.embeddings import get_embedding_model
from backend.app.rag.vector_store import SupabaseVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ingest")


def run_ingestion(
    input_dir: Path = None,
    force_update: bool = False,
    dry_run: bool = False
):
    target_dir = input_dir or settings.data_raw_dir
    if not target_dir.exists():
        logger.error("Raw data directory does not exist: %s", target_dir)
        return

    # Check Supabase connectivity if not in dry-run mode
    vector_store = None
    if not dry_run:
        if not settings.supabase_url or not (settings.supabase_service_role_key or settings.supabase_key):
            logger.warning(
                "Supabase credentials are not configured in .env! "
                "Running in --dry-run mode to process, chunk, and embed documents locally."
            )
            dry_run = True
        else:
            try:
                vector_store = SupabaseVectorStore(admin=True)
                logger.info("Connected to Supabase at: %s", settings.supabase_url)
            except Exception as e:
                logger.error("Failed to connect to Supabase: %s. Falling back to --dry-run.", e)
                dry_run = True

    chunker = AutomotiveChunker()
    embedding_model = get_embedding_model()

    supported_extensions = [".pdf", ".md", ".txt"]
    doc_files = [f for f in target_dir.iterdir() if f.suffix.lower() in supported_extensions]

    if not doc_files:
        logger.warning("No documents found in %s", target_dir)
        return

    logger.info("Found %d automotive documents in %s", len(doc_files), target_dir)

    total_chunks_processed = 0
    manifest = []
    all_chunks = []

    for file_path in doc_files:
        logger.info("--------------------------------------------------")
        logger.info("Processing document: %s", file_path.name)
        try:
            doc_data = DocumentLoader.load_document(file_path)
            meta = doc_data["metadata"]
            content_hash = doc_data["content_hash"]
            blocks = doc_data["blocks"]

            logger.info("Extracted %d blocks from '%s'", len(blocks), meta.title)

            # Chunk the blocks
            chunks = chunker.chunk_text_blocks(blocks)
            logger.info("Generated %d chunks (chunk_size=%d, overlap=%d)", len(chunks), chunker.chunk_size, chunker.chunk_overlap)

            # Generate embeddings
            texts_to_embed = [c.content for c in chunks]
            logger.info("Generating 384-dimensional embeddings with all-MiniLM-L6-v2...")
            embeddings = embedding_model.embed_texts(texts_to_embed)

            for idx, chunk in enumerate(chunks):
                chunk.embedding = embeddings[idx]

            # Upload to Supabase if connected
            doc_id = f"local-doc-{content_hash[:8]}"
            uploaded_count = len(chunks)
            if not dry_run and vector_store:
                doc_id, is_new_or_updated = vector_store.upsert_document(
                    metadata=meta,
                    content_hash=content_hash,
                    force_update=force_update
                )
                if is_new_or_updated:
                    uploaded_count = vector_store.insert_chunks(doc_id, chunks)
                    logger.info("Successfully uploaded %d chunks to Supabase for document %s", uploaded_count, doc_id)
                else:
                    logger.info("Document '%s' already indexed in Supabase. Skipped chunk re-upload (use --force to override).", meta.title)

            total_chunks_processed += len(chunks)

            manifest.append({
                "file_name": file_path.name,
                "title": meta.title,
                "manufacturer": meta.manufacturer,
                "vehicle_model": meta.vehicle_model,
                "document_type": meta.document_type,
                "content_hash": content_hash,
                "document_id": doc_id,
                "chunks_count": len(chunks),
                "sections": list(set(c.section for c in chunks if c.section)),
                "pages": list(set(c.page_number for c in chunks if c.page_number)),
            })

            for c in chunks:
                all_chunks.append({
                    "id": f"{doc_id}-{c.chunk_index}",
                    "document_id": doc_id,
                    "document_title": meta.title,
                    "manufacturer": meta.manufacturer,
                    "vehicle_model": meta.vehicle_model,
                    "document_type": meta.document_type,
                    "content": c.content,
                    "section": c.section,
                    "page_number": c.page_number,
                    "chunk_index": c.chunk_index,
                    "embedding": c.embedding,
                })

        except Exception as e:
            logger.error("Failed to process %s: %s", file_path.name, e, exc_info=True)

    # Save local manifest and offline knowledge base
    settings.data_processed_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = settings.data_processed_dir / "ingestion_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    kb_path = settings.data_processed_dir / "local_knowledge_base.json"
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f)

    logger.info("==================================================")
    logger.info("Ingestion completed: %d documents, %d total chunks processed.", len(doc_files), total_chunks_processed)
    logger.info("Audit manifest saved to: %s", manifest_path)
    logger.info("Local knowledge base backup saved to: %s", kb_path)
    if dry_run:
        logger.info("Notice: Ran in DRY-RUN mode. Set SUPABASE_URL and SUPABASE_KEY in .env to upload to Supabase.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest automotive service manuals into vector database.")
    parser.add_argument("--dir", type=Path, default=None, help="Directory containing raw documents.")
    parser.add_argument("--force", action="store_true", help="Force re-upload of existing documents.")
    parser.add_argument("--dry-run", action="store_true", help="Run extraction, chunking, and embedding without uploading to Supabase.")
    args = parser.parse_args()

    run_ingestion(input_dir=args.dir, force_update=args.force, dry_run=args.dry_run)
