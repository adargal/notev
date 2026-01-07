"""
Unit tests for hybrid vector store module.
"""
import unittest
import numpy as np
from notev_backend.modules.vector_store import VectorStore
from notev_backend.modules.embedding_providers import EmbeddingProvider, SimpleHashEmbeddingProvider
from notev_backend.modules.bm25_search import BM25Index


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for fast testing."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    def embed(self, texts, input_type="document"):
        """Generate deterministic embeddings based on text hash."""
        embeddings = []
        for text in texts:
            # Create deterministic embedding from text hash
            np.random.seed(hash(text) % (2**32))
            emb = np.random.randn(self._dimension).astype(np.float32)
            # Normalize
            emb = emb / np.linalg.norm(emb)
            embeddings.append(emb)
        return embeddings

    @property
    def dimension(self):
        return self._dimension

    @property
    def name(self):
        return "mock"


class TestVectorStore(unittest.TestCase):
    """Test cases for VectorStore class."""

    def setUp(self):
        """Set up test fixtures with mock embedding provider."""
        self.store = VectorStore(
            embedding_provider=MockEmbeddingProvider(),
            search_mode="hybrid"
        )

    def test_add_and_retrieve_document(self):
        """Test adding a document and retrieving its chunks."""
        doc_id = "test_doc_1"
        chunks = [
            {'text': 'This is chunk one.', 'chunk_index': 0},
            {'text': 'This is chunk two.', 'chunk_index': 1}
        ]
        metadata = {'filename': 'test.txt', 'type': 'global'}

        self.store.add_document(doc_id, chunks, metadata)

        # Verify document was added
        retrieved_chunks = self.store.get_document_chunks(doc_id)
        self.assertEqual(len(retrieved_chunks), 2)
        self.assertEqual(retrieved_chunks[0]['text'], 'This is chunk one.')

    def test_remove_document(self):
        """Test removing a document."""
        doc_id = "test_doc_2"
        chunks = [{'text': 'Test chunk', 'chunk_index': 0}]

        self.store.add_document(doc_id, chunks)
        self.store.remove_document(doc_id)

        # Verify document was removed
        retrieved_chunks = self.store.get_document_chunks(doc_id)
        self.assertEqual(len(retrieved_chunks), 0)

    def test_list_documents(self):
        """Test listing all documents."""
        self.store.clear()

        doc1_chunks = [{'text': 'Doc 1 chunk', 'chunk_index': 0}]
        doc2_chunks = [{'text': 'Doc 2 chunk', 'chunk_index': 0}]

        self.store.add_document("doc1", doc1_chunks, {'filename': 'file1.txt'})
        self.store.add_document("doc2", doc2_chunks, {'filename': 'file2.txt'})

        docs = self.store.list_documents()
        self.assertEqual(len(docs), 2)

        doc_ids = [doc['doc_id'] for doc in docs]
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)

    def test_search_basic(self):
        """Test basic search functionality."""
        chunks = [
            {'text': 'The quick brown fox jumps over the lazy dog.', 'chunk_index': 0},
            {'text': 'Python programming is fun and powerful.', 'chunk_index': 1}
        ]

        self.store.clear()
        self.store.add_document("search_test", chunks)

        # Search should return results
        results = self.store.search("fox", top_k=1)
        self.assertGreater(len(results), 0)

    def test_search_with_filter(self):
        """Test search with document ID filter."""
        self.store.clear()

        chunks1 = [{'text': 'Document one content', 'chunk_index': 0}]
        chunks2 = [{'text': 'Document two content', 'chunk_index': 0}]

        self.store.add_document("doc1", chunks1)
        self.store.add_document("doc2", chunks2)

        # Search only in doc1
        results = self.store.search("content", top_k=5, filter_doc_ids=["doc1"])

        # All results should be from doc1
        for result in results:
            self.assertEqual(result['doc_id'], "doc1")

    def test_search_modes(self):
        """Test different search modes: hybrid, vector, bm25."""
        self.store.clear()

        chunks = [
            {'text': 'Machine learning algorithms for data science', 'chunk_index': 0},
            {'text': 'Deep neural networks and artificial intelligence', 'chunk_index': 1},
            {'text': 'Python programming basics tutorial', 'chunk_index': 2}
        ]

        self.store.add_document("ml_docs", chunks)

        # All search modes should return results
        hybrid_results = self.store.search("AI machine learning", search_mode="hybrid")
        vector_results = self.store.search("AI machine learning", search_mode="vector")
        bm25_results = self.store.search("AI machine learning", search_mode="bm25")

        self.assertGreater(len(hybrid_results), 0)
        self.assertGreater(len(vector_results), 0)
        self.assertGreater(len(bm25_results), 0)

    def test_clear_store(self):
        """Test clearing the entire store."""
        chunks = [{'text': 'Test', 'chunk_index': 0}]
        self.store.add_document("test", chunks)

        self.store.clear()

        docs = self.store.list_documents()
        self.assertEqual(len(docs), 0)

    def test_get_stats(self):
        """Test getting store statistics."""
        self.store.clear()

        chunks = [
            {'text': 'Chunk 1', 'chunk_index': 0},
            {'text': 'Chunk 2', 'chunk_index': 1}
        ]
        self.store.add_document("stats_test", chunks)

        stats = self.store.get_stats()
        self.assertEqual(stats['total_chunks'], 2)
        self.assertEqual(stats['total_documents'], 1)
        self.assertEqual(stats['embedding_provider'], 'mock')
        self.assertEqual(stats['search_mode'], 'hybrid')


class TestBM25Index(unittest.TestCase):
    """Test cases for BM25 index."""

    def setUp(self):
        """Set up test fixtures."""
        self.index = BM25Index()

    def test_add_and_search(self):
        """Test adding documents and searching."""
        docs = [
            {'text': 'The quick brown fox jumps'},
            {'text': 'The lazy dog sleeps'},
            {'text': 'Python programming language'}
        ]

        self.index.add_documents(docs)

        results = self.index.search("fox", top_k=2)
        self.assertGreater(len(results), 0)
        # First result should be the fox document (index 0)
        self.assertEqual(results[0][0], 0)

    def test_hebrew_tokenization(self):
        """Test Hebrew text tokenization."""
        tokens = self.index._tokenize("שלום עולם hello world")

        # Should contain both Hebrew and English tokens
        self.assertIn("שלום", tokens)
        self.assertIn("עולם", tokens)
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)

    def test_hebrew_search(self):
        """Test searching Hebrew documents."""
        docs = [
            {'text': 'שלום עולם, זהו מסמך בעברית'},
            {'text': 'This is an English document'},
            {'text': 'מסמך נוסף בעברית עם תוכן שונה'}
        ]

        self.index.add_documents(docs)

        # Search for exact token "מסמך" (document) which appears in docs 0 and 2
        results = self.index.search("מסמך", top_k=3)
        self.assertGreater(len(results), 0)

        # Hebrew documents should rank higher
        hebrew_indices = [r[0] for r in results if r[1] > 0]
        self.assertIn(0, hebrew_indices)  # First doc has "מסמך"
        self.assertIn(2, hebrew_indices)  # Third doc has "מסמך"

    def test_remove_document(self):
        """Test removing a document from the index."""
        docs = [
            {'text': 'Document one'},
            {'text': 'Document two'},
            {'text': 'Document three'}
        ]

        self.index.add_documents(docs)
        self.assertEqual(len(self.index), 3)

        self.index.remove_document(1)  # Remove middle document
        self.assertEqual(len(self.index), 2)

    def test_clear(self):
        """Test clearing the index."""
        docs = [{'text': 'Test document'}]
        self.index.add_documents(docs)

        self.index.clear()
        self.assertEqual(len(self.index), 0)


class TestEmbeddingProviders(unittest.TestCase):
    """Test cases for embedding providers."""

    def test_simple_hash_provider(self):
        """Test SimpleHashEmbeddingProvider."""
        provider = SimpleHashEmbeddingProvider(dimension=512)

        embeddings = provider.embed(["Hello world", "Test text"])

        self.assertEqual(len(embeddings), 2)
        self.assertEqual(embeddings[0].shape[0], 512)
        self.assertEqual(provider.dimension, 512)
        self.assertEqual(provider.name, "simple-hash")

    def test_simple_hash_normalization(self):
        """Test that SimpleHashEmbeddingProvider normalizes vectors."""
        provider = SimpleHashEmbeddingProvider()

        embedding = provider.embed(["Some test text"])[0]
        norm = np.linalg.norm(embedding)

        # Should be normalized (norm ≈ 1.0)
        self.assertAlmostEqual(norm, 1.0, places=5)


if __name__ == '__main__':
    unittest.main()
