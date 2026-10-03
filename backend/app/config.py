import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # Supabase credentials
    supabase_url: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = Field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    supabase_service_role_key: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    # Embedding model configuration
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_dimension: int = Field(default=384)

    # Document Chunking
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=80)

    # Retrieval
    rag_top_k: int = Field(default=5)
    rag_similarity_threshold: float = Field(default=0.25)

    # API Server
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)

    # Local paths
    data_raw_dir: Path = BASE_DIR / "data" / "raw"
    data_processed_dir: Path = BASE_DIR / "data" / "processed"
    models_dir: Path = BASE_DIR / "models"

    model_config = {
        "env_file": str(env_path),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
