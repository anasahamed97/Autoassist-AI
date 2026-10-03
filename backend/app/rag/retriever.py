import time
import logging
from typing import List, Optional, Dict, Any
from backend.app.config import settings
from backend.app.database import get_supabase_client
from backend.app.rag.embeddings import get_embedding_model
from backend.app.schemas.rag import RAGSearchResultItem, RAGSearchResponse

logger = logging.getLogger(__name__)


class AutomotiveRetriever:
    """
    Performs semantic vector search against automotive service documentation
    stored in Supabase pgvector. Supports seamless local fallback for offline evaluation.
    """

    def __init__(self):
        self.embedding_model = get_embedding_model()
        self._supabase = None
        self._local_chunks = None

        if settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key):
            try:
                self._supabase = get_supabase_client(admin=False)
                logger.info("Retriever connected to Supabase PostgreSQL at %s", settings.supabase_url)
            except Exception as e:
                logger.warning("Could not initialize Supabase client: %s. Using local knowledge base.", e)

    def _load_local_chunks(self) -> List[Dict[str, Any]]:
        if self._local_chunks is not None:
            return self._local_chunks

        kb_path = settings.data_processed_dir / "local_knowledge_base.json"
        if kb_path.exists():
            import json
            with open(kb_path, "r", encoding="utf-8") as f:
                self._local_chunks = json.load(f)
            logger.info("Loaded %d chunks from local knowledge base", len(self._local_chunks))
        else:
            self._local_chunks = []
        return self._local_chunks

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RAGSearchResponse:
        start_time = time.perf_counter()

        k = top_k or settings.rag_top_k
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.rag_similarity_threshold
        )
        filter_meta = filters or {}

        # 1. Generate query embedding (384-dimensional normalized vector)
        query_vector = self.embedding_model.embed_query(query)

        items: List[RAGSearchResultItem] = []

        # 2. Try Supabase pgvector RPC if client is active
        if self._supabase is not None:
            try:
                rpc_params = {
                    "query_embedding": query_vector,
                    "match_threshold": float(threshold),
                    "match_count": int(k),
                    "filter_metadata": filter_meta,
                }
                response = self._supabase.rpc("match_document_chunks", rpc_params).execute()
                rows = response.data or []
                for row in rows:
                    items.append(
                        RAGSearchResultItem(
                            content=row.get("content", ""),
                            similarity=float(row.get("similarity", 0.0)),
                            document_title=row.get("document_title"),
                            manufacturer=row.get("manufacturer"),
                            vehicle_model=row.get("vehicle_model"),
                            model_year=row.get("model_year"),
                            document_type=row.get("document_type"),
                            section=row.get("section"),
                            page_number=row.get("page_number"),
                            source=row.get("source"),
                            source_url=row.get("source_url"),
                        )
                    )
            except Exception as e:
                logger.warning(
                    "Supabase RPC match_document_chunks failed: %s. Falling back to local knowledge base.", e
                )

        # 3. Fallback to local vector search if Supabase returned no rows or is not configured
        if not items:
            local_chunks = self._load_local_chunks()
            if local_chunks:
                import numpy as np
                q_vec = np.array(query_vector, dtype=np.float32)
                scored_chunks = []
                for chunk in local_chunks:
                    emb = chunk.get("embedding")
                    if not emb:
                        continue
                    # Dot product of normalized vectors equals cosine similarity
                    sim = float(np.dot(q_vec, np.array(emb, dtype=np.float32)))
                    if sim >= threshold:
                        scored_chunks.append((sim, chunk))

                # Sort by similarity descending
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                top_matches = scored_chunks[:k]

                for sim, chunk in top_matches:
                    items.append(
                        RAGSearchResultItem(
                            content=chunk.get("content", ""),
                            similarity=round(sim, 4),
                            document_title=chunk.get("document_title"),
                            manufacturer=chunk.get("manufacturer"),
                            vehicle_model=chunk.get("vehicle_model"),
                            model_year=chunk.get("model_year"),
                            document_type=chunk.get("document_type"),
                            section=chunk.get("section"),
                            page_number=chunk.get("page_number"),
                            source=chunk.get("source", "Automotive Knowledge Base"),
                            source_url=chunk.get("source_url"),
                        )
                    )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return RAGSearchResponse(
            query=query,
            results=items,
            total_results=len(items),
            latency_ms=latency_ms,
        )
