"""
Global documents manager for handling organization-wide baseline documents.
Global documents are available to all workspaces.
"""
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class GlobalDocsManager:
    """Manages global documents accessible to all workspaces."""

    def __init__(self, global_docs_path: Path):
        """
        Initialize global documents manager.

        Args:
            global_docs_path: Base path for global documents storage
        """
        self.global_docs_path = Path(global_docs_path)
        self.global_docs_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.global_docs_path / 'global_docs_metadata.json'

        # Load or initialize metadata
        self.metadata = self._load_metadata()

    def add_document(self, source_file: str, doc_metadata: Dict[str, Any]) -> Optional[str]:
        """
        Add a global document.

        Args:
            source_file: Path to source document file
            doc_metadata: Document metadata

        Returns:
            Document ID if successful, None otherwise
        """
        doc_id = str(uuid.uuid4())
        source_path = Path(source_file)

        # Copy document to global docs directory
        dest_file = self.global_docs_path / f"{doc_id}_{source_path.name}"

        try:
            shutil.copy2(source_file, dest_file)
        except Exception as e:
            print(f"Error copying document: {e}")
            return None

        # Add document metadata
        doc_entry = {
            'id': doc_id,
            'original_filename': source_path.name,
            'stored_filename': dest_file.name,
            'file_path': str(dest_file),
            'added_at': datetime.utcnow().isoformat(),
            **doc_metadata
        }

        self.metadata['documents'].append(doc_entry)
        self.metadata['updated_at'] = datetime.utcnow().isoformat()

        self._save_metadata()

        return doc_id

    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a global document.

        Args:
            doc_id: Document identifier

        Returns:
            True if successful, False otherwise
        """
        # Find and remove document metadata
        doc_entry = None
        for i, doc in enumerate(self.metadata['documents']):
            if doc['id'] == doc_id:
                doc_entry = self.metadata['documents'].pop(i)
                break

        if not doc_entry:
            return False

        # Delete document file
        doc_file = Path(doc_entry['file_path'])
        if doc_file.exists():
            try:
                doc_file.unlink()
            except Exception as e:
                print(f"Error deleting document file: {e}")

        self.metadata['updated_at'] = datetime.utcnow().isoformat()
        self._save_metadata()

        return True

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get global document metadata.

        Args:
            doc_id: Document identifier

        Returns:
            Document metadata or None if not found
        """
        for doc in self.metadata['documents']:
            if doc['id'] == doc_id:
                return doc
        return None

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all global documents.

        Returns:
            List of document metadata dictionaries
        """
        return self.metadata.get('documents', [])

    def update_document_metadata(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update global document metadata.

        Args:
            doc_id: Document identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        for doc in self.metadata['documents']:
            if doc['id'] == doc_id:
                doc.update(updates)
                doc['updated_at'] = datetime.utcnow().isoformat()
                self.metadata['updated_at'] = datetime.utcnow().isoformat()
                self._save_metadata()
                return True
        return False

    def _load_metadata(self) -> Dict[str, Any]:
        """Load global documents metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading global docs metadata: {e}")

        # Return default structure if file doesn't exist or is corrupt
        return {
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'documents': []
        }

    def _save_metadata(self):
        """Save global documents metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving global docs metadata: {e}")
            raise
