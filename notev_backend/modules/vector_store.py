"""
Hybrid vector store combining BM25 keyword search and semantic vector search.
Uses local embeddings with sentence-transformers for free, offline operation.
"""
import numpy as np
from typing import List, Dict, Any, Optional

from .embedding_providers import (
    EmbeddingProvider,
    LocalEmbeddingProvider,
    SimpleHashEmbeddingProvider,
    create_embedding_provider
)
from .bm25_search import BM25Index


class VectorStore:
    """
    Hybrid vector store with BM25 + semantic search.
    Uses Reciprocal Rank Fusion to combine results.
    """

    def __init__(self,
                 embedding_provider: Optional[EmbeddingProvider] = None,
                 local_model: str = "intfloat/multilingual-e5-small",
                 model_cache_dir: str = None,
                 search_mode: str = "hybrid"):
        """
        Initialize hybrid vector store.

        Args:
            embedding_provider: Custom embedding provider (overrides other settings)
            local_model: Local model name (default: multilingual-e5-small)
            model_cache_dir: Directory to cache local models
            search_mode: Search mode - "hybrid", "vector", or "bm25"
        """
        # Initialize embedding provider
        if embedding_provider:
            self.embedding_provider = embedding_provider
        else:
            self.embedding_provider = create_embedding_provider(
                local_model=local_model,
                model_cache_dir=model_cache_dir
            )

        self.search_mode = search_mode
        print(f"VectorStore initialized with: {self.embedding_provider.name}")
        print(f"Search mode: {self.search_mode}")

        # In-memory vector storage
        self.embeddings = []  # List of numpy arrays
        self.documents = []  # List of document chunks with metadata
        self.doc_id_to_indices = {}  # Map document IDs to their chunk indices

        # BM25 index for keyword search
        self.bm25_index = BM25Index()

    def add_document(self, doc_id: str, chunks: List[Dict[str, Any]],
                     metadata: Dict[str, Any] = None):
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
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_provider.embed(texts, input_type="document")

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

            # Add to BM25 index
            self.bm25_index.add_document({'text': chunk['text']})

        # Map document ID to its chunk indices
        if doc_id in self.doc_id_to_indices:
            self.doc_id_to_indices[doc_id].extend(indices)
        else:
            self.doc_id_to_indices[doc_id] = indices

        print(f"Added document {doc_id} with {len(chunks)} chunks")

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

        # Remove from BM25 index
        self.bm25_index.remove_documents_by_indices(list(indices_to_remove))

        # Update doc_id_to_indices mapping
        del self.doc_id_to_indices[doc_id]
        for did, indices in self.doc_id_to_indices.items():
            self.doc_id_to_indices[did] = [
                index_mapping[idx] for idx in indices if idx in index_mapping
            ]

    def search(self, query: str, top_k: int = 5,
               filter_doc_ids: Optional[List[str]] = None,
               search_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query text
            top_k: Number of top results to return
            filter_doc_ids: Optional list of document IDs to restrict search to
            search_mode: Override default search mode ("hybrid", "vector", "bm25")

        Returns:
            List of search results with text, metadata, and similarity scores
        """
        if not self.documents:
            print("No documents in vector store to search")
            return []

        mode = search_mode or self.search_mode
        print(f"\nSearching ({mode}): '{query[:60]}...'")
        print(f"Total chunks: {len(self.documents)}")

        # Filter indices if doc_ids specified
        if filter_doc_ids:
            valid_indices = set()
            for doc_id in filter_doc_ids:
                if doc_id in self.doc_id_to_indices:
                    valid_indices.update(self.doc_id_to_indices[doc_id])
            valid_indices = list(valid_indices)
            print(f"Filtered to {len(valid_indices)} chunks from {len(filter_doc_ids)} documents")
        else:
            valid_indices = list(range(len(self.documents)))

        if not valid_indices:
            print("No valid chunks found after filtering")
            return []

        # Get scores based on search mode
        if mode == "bm25":
            final_scores = self._bm25_search(query, valid_indices)
        elif mode == "vector":
            final_scores = self._vector_search(query, valid_indices)
        else:  # hybrid (default)
            final_scores = self._hybrid_search(query, valid_indices)

        # Sort by score descending
        sorted_indices = sorted(final_scores.keys(),
                                key=lambda i: final_scores[i],
                                reverse=True)

        # Get top_k results
        results = []
        for idx in sorted_indices[:top_k]:
            doc = self.documents[idx].copy()
            doc['similarity_score'] = float(final_scores[idx])
            results.append(doc)

        # Log results
        print(f"Top {len(results)} results:")
        for i, result in enumerate(results, 1):
            filename = result.get('metadata', {}).get('filename', 'unknown')
            score = result['similarity_score']
            print(f"  {i}. {filename} (score: {score:.4f})")

        return results

    def _vector_search(self, query: str, valid_indices: List[int]) -> Dict[int, float]:
        """
        Perform vector similarity search.

        Args:
            query: Search query
            valid_indices: Indices to search within

        Returns:
            Dictionary mapping index to similarity score
        """
        query_embedding = self.embedding_provider.embed([query], input_type="query")[0]

        scores = {}
        for idx in valid_indices:
            similarity = self._cosine_similarity(query_embedding, self.embeddings[idx])
            scores[idx] = similarity

        return scores

    def _bm25_search(self, query: str, valid_indices: List[int]) -> Dict[int, float]:
        """
        Perform BM25 keyword search.

        Args:
            query: Search query
            valid_indices: Indices to search within

        Returns:
            Dictionary mapping index to normalized BM25 score
        """
        bm25_scores = self.bm25_index.get_scores(query, valid_indices)

        # Normalize BM25 scores to [0, 1]
        if bm25_scores:
            max_score = max(bm25_scores.values()) if bm25_scores.values() else 1
            if max_score > 0:
                return {idx: score / max_score for idx, score in bm25_scores.items()}

        return {}

    def _hybrid_search(self, query: str, valid_indices: List[int]) -> Dict[int, float]:
        """
        Combine vector and BM25 search using Reciprocal Rank Fusion (RRF).

        RRF is a robust score fusion method that doesn't require tuning.
        Score = sum(1 / (k + rank)) for each ranking method.

        Args:
            query: Search query
            valid_indices: Indices to search within

        Returns:
            Dictionary mapping index to RRF score
        """
        vector_scores = self._vector_search(query, valid_indices)
        bm25_scores = self._bm25_search(query, valid_indices)

        # RRF constant (standard value from literature)
        k = 60

        # Get rankings (sorted indices by score, descending)
        vector_ranking = sorted(vector_scores.keys(),
                                key=lambda i: vector_scores.get(i, 0),
                                reverse=True)
        bm25_ranking = sorted(bm25_scores.keys(),
                              key=lambda i: bm25_scores.get(i, 0),
                              reverse=True)

        # Calculate RRF scores
        rrf_scores = {}

        for rank, idx in enumerate(vector_ranking):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank + 1)

        for rank, idx in enumerate(bm25_ranking):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank + 1)

        return rrf_scores

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score
        """
        # If vectors are already normalized, dot product = cosine similarity
        dot_product = np.dot(vec1, vec2)

        # Safety check for non-normalized vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

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
        self.bm25_index.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with store statistics
        """
        return {
            'total_chunks': len(self.documents),
            'total_documents': len(self.doc_id_to_indices),
            'embedding_dimension': self.embedding_provider.dimension,
            'embedding_provider': self.embedding_provider.name,
            'search_mode': self.search_mode,
            'bm25_stats': self.bm25_index.get_stats(),
            'documents': self.list_documents()
        }
