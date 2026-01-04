"""
Unit tests for document processor module.
"""
import unittest
import tempfile
from pathlib import Path
from notev_backend.modules.document_processor import DocumentProcessor


class TestDocumentProcessor(unittest.TestCase):
    """Test cases for DocumentProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)

    def test_create_chunks_basic(self):
        """Test basic text chunking."""
        text = "This is a test. " * 20  # 320 characters
        chunks = self.processor._create_chunks(text)

        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks, list)
        for chunk in chunks:
            self.assertIn('text', chunk)
            self.assertIn('chunk_index', chunk)

    def test_create_chunks_empty(self):
        """Test chunking with empty text."""
        chunks = self.processor._create_chunks("")
        self.assertEqual(len(chunks), 0)

    def test_extract_text_from_txt(self):
        """Test text extraction from .txt file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello, World!\nThis is a test.")
            temp_path = Path(f.name)

        try:
            text = self.processor._extract_text_from_txt(temp_path)
            self.assertIn("Hello, World!", text)
            self.assertIn("This is a test.", text)
        finally:
            temp_path.unlink()

    def test_validate_file_txt(self):
        """Test file validation for .txt files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            is_valid, error = self.processor.validate_file(str(temp_path))
            self.assertTrue(is_valid)
            self.assertEqual(error, "")
        finally:
            temp_path.unlink()

    def test_validate_file_unsupported(self):
        """Test file validation with unsupported format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            is_valid, error = self.processor.validate_file(str(temp_path))
            self.assertFalse(is_valid)
            self.assertIn("Unsupported format", error)
        finally:
            temp_path.unlink()

    def test_validate_file_nonexistent(self):
        """Test file validation with non-existent file."""
        is_valid, error = self.processor.validate_file("/nonexistent/file.txt")
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A" * 200
        chunks = self.processor._create_chunks(text)

        if len(chunks) > 1:
            # Check that overlap exists
            chunk1_end = chunks[0]['end_char']
            chunk2_start = chunks[1]['start_char']
            overlap = chunk1_end - chunk2_start
            self.assertGreater(overlap, 0)


if __name__ == '__main__':
    unittest.main()
