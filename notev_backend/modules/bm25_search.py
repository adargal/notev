"""
BM25 keyword search with Hebrew and English support.
Provides lexical search to complement semantic vector search.
"""
from typing import List, Dict, Any, Optional, Tuple
import re
from rank_bm25 import BM25Okapi


class BM25Index:
    """
    BM25 index for keyword-based document search.
    Supports Hebrew and English text with proper tokenization.
    """

    def __init__(self):
        """Initialize empty BM25 index."""
        self.documents = []  # Store document metadata
        self.corpus = []  # Tokenized documents
        self.index = None

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 search.
        Handles both Hebrew and English text properly.

        Args:
            text: Input text to tokenize

        Returns:
            List of tokens
        """
        # Lowercase for English consistency
        text = text.lower()

        # Split on whitespace and punctuation, keeping:
        # - Word characters (\w includes letters, digits, underscore)
        # - Hebrew characters: \u0590-\u05FF (Hebrew block)
        # - Hebrew extended: \uFB1D-\uFB4F (Hebrew presentation forms)
        tokens = re.findall(r'[\w\u0590-\u05FF\uFB1D-\uFB4F]+', text, re.UNICODE)

        # Filter very short tokens, but keep Hebrew single chars (can be meaningful)
        filtered_tokens = []
        for t in tokens:
            # Keep if: length > 1, OR it's a Hebrew character
            if len(t) > 1 or ('\u0590' <= t <= '\u05FF') or ('\uFB1D' <= t <= '\uFB4F'):
                filtered_tokens.append(t)

        return filtered_tokens

    def add_document(self, doc: Dict[str, Any]):
        """
        Add a single document to the index.

        Args:
            doc: Document dict with 'text' key
        """
        text = doc.get('text', '')
        tokens = self._tokenize(text)
        self.corpus.append(tokens)
        self.documents.append(doc)

        # Rebuild index (necessary for BM25Okapi)
        self._rebuild_index()

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add multiple documents to the BM25 index.

        Args:
            documents: List of document dicts with 'text' key
        """
        for doc in documents:
            text = doc.get('text', '')
            tokens = self._tokenize(text)
            self.corpus.append(tokens)
            self.documents.append(doc)

        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the BM25 index from corpus."""
        if self.corpus:
            self.index = BM25Okapi(self.corpus)
        else:
            self.index = None

    def remove_document(self, index: int):
        """
        Remove document at given index.

        Args:
            index: Index of document to remove
        """
        if 0 <= index < len(self.documents):
            del self.documents[index]
            del self.corpus[index]
            self._rebuild_index()

    def remove_documents_by_indices(self, indices: List[int]):
        """
        Remove multiple documents by their indices.

        Args:
            indices: List of indices to remove
        """
        if not indices:
            return

        # Sort indices in descending order to remove from end first
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.documents):
                del self.documents[idx]
                del self.corpus[idx]

        self._rebuild_index()

    def search(self, query: str, top_k: int = 10,
               valid_indices: Optional[List[int]] = None) -> List[Tuple[int, float]]:
        """
        Search the BM25 index.

        Args:
            query: Search query
            top_k: Number of results to return
            valid_indices: If provided, only search within these indices

        Returns:
            List of (document_index, score) tuples, sorted by score descending
        """
        if not self.index or not self.corpus:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = self.index.get_scores(query_tokens)

        # Get indices and scores
        if valid_indices is not None:
            results = [(i, scores[i]) for i in valid_indices if i < len(scores) and scores[i] > 0]
        else:
            results = [(i, score) for i, score in enumerate(scores) if score > 0]

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_scores(self, query: str, valid_indices: Optional[List[int]] = None) -> Dict[int, float]:
        """
        Get BM25 scores for all documents.

        Args:
            query: Search query
            valid_indices: If provided, only score these indices

        Returns:
            Dictionary mapping document index to score
        """
        if not self.index or not self.corpus:
            return {}

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return {}

        scores = self.index.get_scores(query_tokens)

        if valid_indices is not None:
            return {i: scores[i] for i in valid_indices if i < len(scores)}
        else:
            return {i: score for i, score in enumerate(scores)}

    def clear(self):
        """Clear the index."""
        self.documents = []
        self.corpus = []
        self.index = None

    def __len__(self) -> int:
        """Return number of documents in index."""
        return len(self.documents)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the BM25 index.

        Returns:
            Dictionary with index statistics
        """
        total_tokens = sum(len(doc_tokens) for doc_tokens in self.corpus)
        avg_tokens = total_tokens / len(self.corpus) if self.corpus else 0

        return {
            'num_documents': len(self.documents),
            'total_tokens': total_tokens,
            'avg_tokens_per_doc': avg_tokens
        }
