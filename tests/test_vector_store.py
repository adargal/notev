"""
Unit tests for vector store module.
"""
import unittest
from notev_backend.modules.vector_store import VectorStore


class TestVectorStore(unittest.TestCase):
    """Test cases for VectorStore class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a dummy API key for testing
        self.store = VectorStore(api_key="test-key", embedding_model="test-model")

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


if __name__ == '__main__':
    unittest.main()
