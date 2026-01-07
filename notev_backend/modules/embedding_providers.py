"""
Embedding provider for local sentence-transformers models.
Provides free, offline embeddings with multilingual support.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
import os
import sys


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str], input_type: str = "document") -> List[np.ndarray]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            input_type: "document" or "query" (some models handle these differently)

        Returns:
            List of embedding vectors as numpy arrays
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name for logging."""
        pass


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local sentence-transformers embedding provider (free, offline).
    Uses multilingual models that support Hebrew and English.
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small",
                 cache_dir: Optional[str] = None):
        """
        Initialize local embedding provider.

        Args:
            model_name: HuggingFace model name
            cache_dir: Directory to cache model files (defaults to app data dir for EXE)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self._model = None
        self._dimension = None

    def _get_default_cache_dir(self) -> Optional[str]:
        """Get appropriate cache directory for models."""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller EXE - use app data directory
            if os.name == 'nt':  # Windows
                base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                return os.path.join(base, 'Notev', 'models')
            else:  # Linux/Mac
                return os.path.join(os.path.expanduser('~'), '.notev', 'models')
        else:
            # Running as script - use default HuggingFace cache
            return None

    def _ensure_cache_dir(self):
        """Create cache directory if needed."""
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            # Set environment variables for HuggingFace
            os.environ['TRANSFORMERS_CACHE'] = self.cache_dir
            os.environ['HF_HOME'] = self.cache_dir
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = self.cache_dir

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            print(f"Loading local embedding model: {self.model_name}")

            self._ensure_cache_dir()

            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir,
                device='cpu'  # Force CPU for compatibility
            )
            self._dimension = self._model.get_sentence_embedding_dimension()
            print(f"Model loaded successfully. Dimension: {self._dimension}")

    def embed(self, texts: List[str], input_type: str = "document") -> List[np.ndarray]:
        """
        Generate embeddings using local model.

        For E5 models, automatically adds required prefixes:
        - "query: " for queries
        - "passage: " for documents
        """
        self._load_model()

        # E5 models require instruction prefix for best results
        if "e5" in self.model_name.lower():
            if input_type == "query":
                texts = [f"query: {t}" for t in texts]
            else:
                texts = [f"passage: {t}" for t in texts]

        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 10,
            normalize_embeddings=True  # L2 normalize for cosine similarity
        )

        # Ensure we return a list of arrays
        if len(embeddings.shape) == 1:
            return [embeddings.astype(np.float32)]
        return [emb.astype(np.float32) for emb in embeddings]

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._load_model()
        return self._dimension

    @property
    def name(self) -> str:
        return f"local:{self.model_name}"

    def is_model_cached(self) -> bool:
        """Check if model is already downloaded."""
        if not self.cache_dir:
            return True  # Using default cache, assume available

        # Check for model files in cache
        from pathlib import Path
        model_path = Path(self.cache_dir) / self.model_name.replace("/", "--")
        return model_path.exists()

    def download_model(self, show_progress: bool = True):
        """
        Pre-download the model (useful for first-run setup).

        Args:
            show_progress: Whether to show download progress
        """
        print(f"Downloading embedding model: {self.model_name}")
        self._ensure_cache_dir()

        from sentence_transformers import SentenceTransformer

        # This will download if not present
        self._model = SentenceTransformer(
            self.model_name,
            cache_folder=self.cache_dir,
            device='cpu'
        )
        self._dimension = self._model.get_sentence_embedding_dimension()
        print(f"Model downloaded and ready. Dimension: {self._dimension}")


class SimpleHashEmbeddingProvider(EmbeddingProvider):
    """
    Simple hash-based embedding provider (fallback).
    Only provides basic keyword matching, not semantic search.
    Used when sentence-transformers is not installed.
    """

    def __init__(self, dimension: int = 1024):
        """
        Initialize simple embedding provider.

        Args:
            dimension: Embedding dimension
        """
        self._dimension = dimension

    def embed(self, texts: List[str], input_type: str = "document") -> List[np.ndarray]:
        """Generate simple hash-based embeddings."""
        embeddings = []
        for text in texts:
            embedding = self._hash_embed(text)
            embeddings.append(embedding)
        return embeddings

    def _hash_embed(self, text: str) -> np.ndarray:
        """Create hash-based embedding for a single text."""
        words = text.lower().split()
        embedding = np.zeros(self._dimension, dtype=np.float32)

        for word in words:
            # Hash word to embedding dimension
            hash_val = hash(word) % self._dimension
            embedding[hash_val] += 1.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def name(self) -> str:
        return "simple-hash"


def create_embedding_provider(
    local_model: str = "intfloat/multilingual-e5-small",
    model_cache_dir: Optional[str] = None
) -> EmbeddingProvider:
    """
    Factory function to create the embedding provider.

    Args:
        local_model: Model name for local embeddings
        model_cache_dir: Cache directory for local models

    Returns:
        Configured EmbeddingProvider instance
    """
    try:
        # Try to import sentence-transformers
        import sentence_transformers
        provider = LocalEmbeddingProvider(
            model_name=local_model,
            cache_dir=model_cache_dir
        )
        print(f"Using local embeddings: {local_model}")
        return provider
    except ImportError:
        print("WARNING: sentence-transformers not installed, falling back to simple embeddings")
        print("  Install with: pip install sentence-transformers")
        return SimpleHashEmbeddingProvider()
