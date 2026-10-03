import logging
from typing import List, Dict, Any, Optional
from backend.app.database import get_supabase_client
from backend.app.schemas.rag import DocumentMetadata, DocumentChunk

logger = logging.getLogger(__name__)


class SupabaseVectorStore:
    """
    Manages document and chunk persistence in Supabase PostgreSQL + pgvector.
    Provides idempotent ingestion via content hash deduplication.
    """

    def __init__(self, admin: bool = True):
        self.supabase = get_supabase_client(admin=admin)

    def find_document_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Checks if a document with this content hash already exists."""
        resp = (
            self.supabase.table("documents")
            .select("id, title, content_hash, created_at")
            .eq("content_hash", content_hash)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
        return None

    def upsert_document(
        self,
        metadata: DocumentMetadata,
        content_hash: str,
        force_update: bool = False
    ) -> tuple[str, bool]:
        """
        Idempotently inserts or retrieves a document.
        Returns (document_id, is_new_or_updated).
        """
        existing = self.find_document_by_hash(content_hash)
        if existing and not force_update:
            logger.info("Document already indexed with ID: %s (hash: %s)", existing["id"], content_hash)
            return existing["id"], False

        doc_payload = {
            "title": metadata.title,
            "manufacturer": metadata.manufacturer,
            "vehicle_model": metadata.vehicle_model,
            "model_year": metadata.model_year,
            "document_type": metadata.document_type,
            "source": metadata.source,
            "source_url": metadata.source_url,
            "content_hash": content_hash,
            "metadata": metadata.extra_metadata or {},
        }

        if existing and force_update:
            doc_id = existing["id"]
            logger.info("Updating existing document ID: %s", doc_id)
            self.supabase.table("documents").update(doc_payload).eq("id", doc_id).execute()
            # Delete old chunks for clean replacement
            self.supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
            return doc_id, True

        logger.info("Inserting new document: '%s'", metadata.title)
        resp = self.supabase.table("documents").insert(doc_payload).execute()
        if not resp.data:
            raise RuntimeError(f"Failed to insert document: {doc_payload['title']}")
        return resp.data[0]["id"], True

    def insert_chunks(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        batch_size: int = 50
    ) -> int:
        """
        Inserts document chunks along with their vector embeddings in batches.
        """
        if not chunks:
            return 0

        inserted_count = 0
        total = len(chunks)

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            payloads = []
            for chunk in batch:
                if not chunk.embedding:
                    raise ValueError(f"Chunk at index {chunk.chunk_index} is missing its embedding vector.")

                payloads.append({
                    "document_id": document_id,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                    "chunk_index": chunk.chunk_index,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "metadata": chunk.metadata or {},
                })

            resp = self.supabase.table("document_chunks").insert(payloads).execute()
            if resp.data:
                inserted_count += len(resp.data)
            logger.info("Inserted %d/%d chunks for document %s", min(i + batch_size, total), total, document_id)

        return inserted_count
