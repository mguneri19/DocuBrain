from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Directories
PERSIST_DIRECTORY = Path(os.getenv("PERSIST_DIRECTORY", "storage/chroma_db"))
UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", "storage/uploads"))

# Embeddings
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Chunking - Optimized for better context
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))  # Daha büyük chunk = daha iyi bağlam
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "300"))  # Daha fazla overlap = daha iyi devamlılık

# Retrieval - Optimized settings
SEARCH_TYPE = os.getenv("SEARCH_TYPE", "mmr")  # "mmr" | "similarity"
TOP_K = int(os.getenv("TOP_K", "8"))  # Optimal: 8 chunks
MMR_LAMBDA = float(os.getenv("MMR_LAMBDA", "0.6"))  # Optimal: 0.6 (balance diversity/relevance)

# Models
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

