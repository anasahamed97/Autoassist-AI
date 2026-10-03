from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: str = Field(..., description="Title of the service manual or technical document")
    manufacturer: Optional[str] = Field(None, description="Automotive manufacturer, e.g., Honda, Toyota, Generic")
    vehicle_model: Optional[str] = Field(None, description="Vehicle model, e.g., Civic, Corolla, Generic")
    model_year: Optional[int] = Field(None, description="Model year if applicable")
    document_type: Optional[str] = Field(None, description="e.g., Service Manual, Diagnostic Guide, Technical Bulletin")
    source: Optional[str] = Field(None, description="Original publisher or document source")
    source_url: Optional[str] = Field(None, description="Reference URL or public domain repository link")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    id: Optional[str] = None
    document_id: Optional[str] = None
    content: str = Field(..., description="Extracted text chunk content")
    chunk_index: int = Field(..., description="Index of this chunk within the parent document")
    section: Optional[str] = Field(None, description="Heading or subsystem section")
    page_number: Optional[int] = Field(None, description="Page number where the text appeared")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding representation")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Automotive customer query or symptom description")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Maximum number of relevant chunks to retrieve")
    similarity_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Minimum cosine similarity score filter"
    )
    manufacturer: Optional[str] = Field(None, description="Filter by manufacturer")
    vehicle_model: Optional[str] = Field(None, description="Filter by vehicle model")


class RAGSearchResultItem(BaseModel):
    content: str
    similarity: float
    document_title: Optional[str] = None
    manufacturer: Optional[str] = None
    vehicle_model: Optional[str] = None
    model_year: Optional[int] = None
    document_type: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResultItem]
    total_results: int
    latency_ms: float
    safety_disclaimer: str = (
        "Technical documentation retrieval for diagnostic assistance only. "
        "Does not constitute an automated certified diagnosis."
    )
