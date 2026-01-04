"""
In-memory vector store for document embeddings and semantic search.
Uses Anthropic's Voyage embeddings via the Claude API.
"""
import numpy as np
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import json


class VectorStore:
    """In-memory vector store with semantic search capabilities."""

    def __init__(self, api_key: str, embedding_model: str = "voyage-3", voyage_api_key: str = None):
        """
        Initialize vector store.

        Args:
            api_key: Anthropic API key (for Claude)
            embedding_model: Name of the embedding model to use
            voyage_api_key: Voyage AI API key (for embeddings). If not provided, falls back to simple embeddings.
        """
        self.client = Anthropic(api_key=api_key)
        self.embedding_model = embedding_model
        self.voyage_api_key = voyage_api_key

        # In-memory storage
        self.embeddings = []  # List of numpy arrays
        self.documents = []  # List of document chunks with metadata
        self.doc_id_to_indices = {}  # Map document IDs to their chunk indices

        # Log embedding configuration
        if self.voyage_api_key:
            print(f"✓ VectorStore initialized with Voyage AI embeddings (model: {self.embedding_model})")
            print(f"  API key present: {self.voyage_api_key[:8]}...{self.voyage_api_key[-4:]}")
        else:
            print("⚠ WARNING: VectorStore initialized WITHOUT Voyage AI - using simple hash-based embeddings")
            print("  For better search quality, add VOYAGE_API_KEY to your .env file")

    def add_document(self, doc_id: str, chunks: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """
        Add a document's chunks to the vector store.

        Args:
            doc_id: Unique identifier for the document
            chunks: List of chunk dictionaries with 'text' key
            metadata: Additional metadata for the document
        """
        if not chunks:
            return

        # Extract texts from chunks
        texts = [chunk['text'] for chunk in chunks]

        # Get embeddings for all chunks
        embeddings = self._get_embeddings(texts)

        # Store starting index for this document
        start_idx = len(self.documents)
        indices = []

        # Add each chunk with its embedding
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_entry = {
                'doc_id': doc_id,
                'chunk_index': chunk.get('chunk_index', i),
                'text': chunk['text'],
                'metadata': metadata or {},
                'chunk_metadata': {k: v for k, v in chunk.items() if k != 'text'}
            }

            self.documents.append(doc_entry)
            self.embeddings.append(embedding)
            indices.append(start_idx + i)

        # Map document ID to its chunk indices
        if doc_id in self.doc_id_to_indices:
            self.doc_id_to_indices[doc_id].extend(indices)
        else:
            self.doc_id_to_indices[doc_id] = indices

    def remove_document(self, doc_id: str):
        """
        Remove a document and all its chunks from the vector store.

        Args:
            doc_id: Document identifier to remove
        """
        if doc_id not in self.doc_id_to_indices:
            return

        # Get indices to remove
        indices_to_remove = set(self.doc_id_to_indices[doc_id])

        # Create new lists without the removed indices
        new_documents = []
        new_embeddings = []
        index_mapping = {}  # Old index -> new index

        for old_idx, (doc, emb) in enumerate(zip(self.documents, self.embeddings)):
            if old_idx not in indices_to_remove:
                new_idx = len(new_documents)
                index_mapping[old_idx] = new_idx
                new_documents.append(doc)
                new_embeddings.append(emb)

        self.documents = new_documents
        self.embeddings = new_embeddings

        # Update doc_id_to_indices mapping
        del self.doc_id_to_indices[doc_id]
        for doc_id, indices in self.doc_id_to_indices.items():
            self.doc_id_to_indices[doc_id] = [
                index_mapping[idx] for idx in indices if idx in index_mapping
            ]

    def search(self, query: str, top_k: int = 5, filter_doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks using semantic similarity.

        Args:
            query: Search query text
            top_k: Number of top results to return
            filter_doc_ids: Optional list of document IDs to restrict search to

        Returns:
            List of search results with text, metadata, and similarity scores
        """
        if not self.documents:
            print("  No documents in vector store to search")
            return []

        print(f"\n🔍 Searching for: '{query[:60]}...'")
        print(f"  Total chunks in store: {len(self.documents)}")

        # Get query embedding
        query_embedding = self._get_embeddings([query])[0]

        # Filter indices if doc_ids specified
        if filter_doc_ids:
            valid_indices = set()
            for doc_id in filter_doc_ids:
                if doc_id in self.doc_id_to_indices:
                    valid_indices.update(self.doc_id_to_indices[doc_id])
            valid_indices = list(valid_indices)
            print(f"  Filtered to {len(valid_indices)} chunks from {len(filter_doc_ids)} documents")
        else:
            valid_indices = list(range(len(self.documents)))
            print(f"  Searching all {len(valid_indices)} chunks")

        if not valid_indices:
            print("  No valid chunks found after filtering")
            return []

        # Calculate similarities for valid documents
        similarities = []
        for idx in valid_indices:
            similarity = self._cosine_similarity(query_embedding, self.embeddings[idx])
            similarities.append((idx, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top_k results
        results = []
        for idx, score in similarities[:top_k]:
            doc = self.documents[idx].copy()
            doc['similarity_score'] = float(score)
            results.append(doc)

        # Log top results
        print(f"  Top {len(results)} results:")
        for i, result in enumerate(results, 1):
            filename = result.get('metadata', {}).get('filename', 'unknown')
            score = result['similarity_score']
            print(f"    {i}. {filename} (score: {score:.4f})")

        return results

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.

        Args:
            doc_id: Document identifier

        Returns:
            List of document chunks
        """
        if doc_id not in self.doc_id_to_indices:
            return []

        indices = self.doc_id_to_indices[doc_id]
        return [self.documents[idx] for idx in indices]

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all unique documents in the store.

        Returns:
            List of document metadata
        """
        doc_info = {}

        for doc in self.documents:
            doc_id = doc['doc_id']
            if doc_id not in doc_info:
                doc_info[doc_id] = {
                    'doc_id': doc_id,
                    'metadata': doc['metadata'],
                    'num_chunks': 0
                }
            doc_info[doc_id]['num_chunks'] += 1

        return list(doc_info.values())

    def clear(self):
        """Clear all documents and embeddings from the store."""
        self.embeddings = []
        self.documents = []
        self.doc_id_to_indices = {}

    def _get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for a list of texts using Voyage AI via Anthropic.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors as numpy arrays
        """
        num_texts = len(texts)

        # Check if Voyage API key is available
        if not self.voyage_api_key:
            # No API key - use simple embeddings
            print(f"⚠ Generating {num_texts} embeddings using SIMPLE HASH-BASED method (no Voyage AI)")
            embeddings = []
            for text in texts:
                embedding = self._simple_text_embedding(text)
                embeddings.append(embedding)
            return embeddings

        try:
            # Try to use Voyage embeddings
            # Note: This requires the voyageai package
            import voyageai

            print(f"→ Generating {num_texts} embeddings using VOYAGE AI ({self.embedding_model})...")

            vo = voyageai.Client(api_key=self.voyage_api_key)

            # Get embeddings in batches
            result = vo.embed(
                texts,
                model=self.embedding_model,
                input_type="document"
            )

            # Convert to numpy arrays
            embeddings = [np.array(emb) for emb in result.embeddings]
            print(f"✓ Successfully generated {len(embeddings)} embeddings via Voyage AI")
            return embeddings

        except ImportError:
            # Fallback to simple embeddings if voyageai not installed
            print("⚠ WARNING: voyageai package not installed. Using simple hash-based embeddings.")
            print("  Install with: pip install voyageai")
            embeddings = []
            for text in texts:
                embedding = self._simple_text_embedding(text)
                embeddings.append(embedding)
            return embeddings

        except Exception as e:
            # Fallback on any API error
            print(f"⚠ ERROR getting embeddings from Voyage AI: {type(e).__name__}: {e}")
            print("  Falling back to simple hash-based embeddings.")
            embeddings = []
            for text in texts:
                embedding = self._simple_text_embedding(text)
                embeddings.append(embedding)
            return embeddings

    def _simple_text_embedding(self, text: str, dim: int = 1024) -> np.ndarray:
        """
        Simple text embedding (placeholder - replace with actual embedding service).

        Args:
            text: Text to embed
            dim: Embedding dimension

        Returns:
            Embedding vector
        """
        # This is a very basic implementation for development
        # In production, replace with actual embedding API calls

        # Use hash-based features for now
        words = text.lower().split()
        embedding = np.zeros(dim)

        for i, word in enumerate(words[:dim]):
            # Simple hash-based feature
            hash_val = hash(word) % dim
            embedding[hash_val] += 1.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with store statistics
        """
        return {
            'total_chunks': len(self.documents),
            'total_documents': len(self.doc_id_to_indices),
            'embedding_dimension': len(self.embeddings[0]) if self.embeddings else 0,
            'documents': self.list_documents()
        }
