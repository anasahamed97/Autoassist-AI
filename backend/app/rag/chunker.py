import re
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.schemas.rag import DocumentChunk


class AutomotiveChunker:
    """
    Intelligent section-aware chunker for automotive service manuals.
    Preserves headings, diagnostic steps, paragraphs, and page numbers.
    """

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_text_blocks(
        self,
        blocks: List[Dict[str, Any]],
        document_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Takes structured blocks (each with 'text', 'page_number', optional 'section').
        Produces an ordered list of DocumentChunk instances.
        """
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        current_section = "General Information"

        for block in blocks:
            text = block.get("text", "").strip()
            page_number = block.get("page_number")
            section_hint = block.get("section")
            if section_hint:
                current_section = section_hint

            if not text:
                continue

            # Split block into paragraphs or structural units
            paragraphs = re.split(r"\n\s*\n", text)

            current_chunk_text = ""
            current_chunk_paras: List[str] = []

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Check if paragraph itself looks like a heading
                if (para.startswith("#") or (para.isupper() and len(para) < 100)) and "\n" not in para:
                    current_section = re.sub(r"^[#\s\-*]+", "", para).strip()

                # If single paragraph is larger than chunk_size, split by sentences
                if len(para) > self.chunk_size:
                    if current_chunk_text:
                        chunks.append(
                            DocumentChunk(
                                document_id=document_id,
                                content=current_chunk_text.strip(),
                                chunk_index=chunk_idx,
                                section=current_section,
                                page_number=page_number,
                            )
                        )
                        chunk_idx += 1
                        current_chunk_text = ""
                        current_chunk_paras = []

                    # Sentence split
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    s_chunk = ""
                    for s in sentences:
                        if len(s_chunk) + len(s) + 1 <= self.chunk_size:
                            s_chunk = f"{s_chunk} {s}".strip()
                        else:
                            if s_chunk:
                                chunks.append(
                                    DocumentChunk(
                                        document_id=document_id,
                                        content=s_chunk.strip(),
                                        chunk_index=chunk_idx,
                                        section=current_section,
                                        page_number=page_number,
                                    )
                                )
                                chunk_idx += 1
                                # Overlap from end of last chunk
                                overlap_text = s_chunk[-self.chunk_overlap:] if self.chunk_overlap < len(s_chunk) else ""
                                s_chunk = f"{overlap_text} {s}".strip()
                            else:
                                s_chunk = s
                    if s_chunk:
                        current_chunk_text = s_chunk
                    continue

                # Normal paragraph accumulation
                projected_len = len(current_chunk_text) + (2 if current_chunk_text else 0) + len(para)
                if projected_len <= self.chunk_size:
                    if current_chunk_text:
                        current_chunk_text = f"{current_chunk_text}\n\n{para}"
                    else:
                        current_chunk_text = para
                    current_chunk_paras.append(para)
                else:
                    # Flush current chunk
                    if current_chunk_text:
                        chunks.append(
                            DocumentChunk(
                                document_id=document_id,
                                content=current_chunk_text.strip(),
                                chunk_index=chunk_idx,
                                section=current_section,
                                page_number=page_number,
                            )
                        )
                        chunk_idx += 1

                    # Apply overlap from previous paragraph if available
                    overlap_prefix = ""
                    if current_chunk_paras and self.chunk_overlap > 0:
                        last_para = current_chunk_paras[-1]
                        if len(last_para) <= self.chunk_overlap:
                            overlap_prefix = last_para
                        else:
                            overlap_prefix = last_para[-self.chunk_overlap:]

                    if overlap_prefix:
                        current_chunk_text = f"...{overlap_prefix}\n\n{para}"
                    else:
                        current_chunk_text = para
                    current_chunk_paras = [para]

            # Flush remaining text in this block
            if current_chunk_text:
                chunks.append(
                    DocumentChunk(
                        document_id=document_id,
                        content=current_chunk_text.strip(),
                        chunk_index=chunk_idx,
                        section=current_section,
                        page_number=page_number,
                    )
                )
                chunk_idx += 1

        return chunks
