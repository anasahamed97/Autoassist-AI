import os
import logging
from pathlib import Path
from typing import List, Union
import numpy as np
import httpx
from tokenizers import Tokenizer
import onnxruntime as ort

from backend.app.config import settings

logger = logging.getLogger(__name__)

# Remote URLs for lightweight sentence-transformers/all-MiniLM-L6-v2 ONNX release
HF_BASE_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main"
ONNX_MODEL_FILE = "onnx/model.onnx"
TOKENIZER_FILE = "tokenizer.json"


class LocalEmbeddingModel:
    """
    Lightweight, production-ready local embedding generator.
    
    Uses ONNX Runtime + HuggingFace Tokenizers to execute
    'sentence-transformers/all-MiniLM-L6-v2' (384 dimensions) completely
    locally on CPU without PyTorch overhead or Windows Smart App Control issues.
    """

    def __init__(self, models_dir: Union[str, Path] = None):
        self.models_dir = Path(models_dir or settings.models_dir) / "all-MiniLM-L6-v2"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.models_dir / "model.onnx"
        self.tokenizer_path = self.models_dir / "tokenizer.json"

        self._session: ort.InferenceSession = None
        self._tokenizer: Tokenizer = None
        self.dimension = settings.embedding_dimension  # 384

    def _ensure_model_files(self):
        """Downloads the ONNX model and tokenizer files if not already cached locally."""
        if not self.tokenizer_path.exists():
            logger.info("Downloading tokenizer from Hugging Face...")
            tok_url = f"{HF_BASE_URL}/{TOKENIZER_FILE}"
            with httpx.Client(follow_redirects=True, timeout=60.0) as client:
                resp = client.get(tok_url)
                resp.raise_for_status()
                with open(self.tokenizer_path, "wb") as f:
                    f.write(resp.content)
            logger.info("Saved tokenizer to %s", self.tokenizer_path)

        if not self.model_path.exists():
            logger.info("Downloading all-MiniLM-L6-v2 ONNX model (~90MB)...")
            model_url = f"{HF_BASE_URL}/{ONNX_MODEL_FILE}"
            with httpx.Client(follow_redirects=True, timeout=120.0) as client:
                with client.stream("GET", model_url) as resp:
                    resp.raise_for_status()
                    with open(self.model_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
            logger.info("Saved ONNX model to %s", self.model_path)

    def load(self):
        """Initializes the ONNX runtime session and tokenizer."""
        if self._session is not None and self._tokenizer is not None:
            return

        self._ensure_model_files()

        # Load tokenizer
        self._tokenizer = Tokenizer.from_file(str(self.tokenizer_path))
        # Ensure padding and truncation to standard 256 tokens for sentence embeddings
        self._tokenizer.enable_truncation(max_length=256)
        self._tokenizer.enable_padding(length=256)

        # Configure ONNX Runtime session for optimal CPU inference
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = min(4, os.cpu_count() or 1)

        self._session = ort.InferenceSession(
            str(self.model_path), sess_options, providers=["CPUExecutionProvider"]
        )
        logger.info("Embedding model loaded successfully (dimension: %d)", self.dimension)

    def _mean_pooling(self, token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        """
        Mean Pooling: take average of token embeddings weighted by attention mask.
        token_embeddings: [batch_size, seq_len, hidden_size]
        attention_mask: [batch_size, seq_len]
        """
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generates normalized 384-dimensional embeddings for a batch of strings.
        """
        if not texts:
            return []

        self.load()

        # Tokenize batch
        encoded = self._tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.array([e.type_ids for e in encoded], dtype=np.int64)

        # Prepare ONNX input dict
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        }

        # Run inference
        outputs = self._session.run(None, inputs)
        token_embeddings = outputs[0]  # [batch_size, seq_len, 384]

        # Mean pooling
        sentence_embeddings = self._mean_pooling(token_embeddings, attention_mask)

        # L2 normalize so cosine similarity equals dot product
        norms = np.linalg.norm(sentence_embeddings, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-12, a_max=None)
        normalized_embeddings = sentence_embeddings / norms

        return normalized_embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Generates normalized 384-dimensional embedding for a single query string.
        """
        result = self.embed_texts([query])
        return result[0] if result else []


# Global singleton instance
_embedding_model: Union[LocalEmbeddingModel, None] = None


def get_embedding_model() -> LocalEmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = LocalEmbeddingModel()
    return _embedding_model
