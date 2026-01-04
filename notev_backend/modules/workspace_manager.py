"""
Workspace management module for handling workspace CRUD operations and persistence.
Each workspace represents a distinct operational case with its own documents and conversations.
"""
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class WorkspaceManager:
    """Manages workspaces with file-based persistence."""

    def __init__(self, workspaces_path: Path):
        """
        Initialize workspace manager.

        Args:
            workspaces_path: Base path for workspace storage
        """
        self.workspaces_path = Path(workspaces_path)
        self.workspaces_path.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new workspace.

        Args:
            name: Workspace name
            description: Optional workspace description

        Returns:
            Workspace metadata dictionary
        """
        workspace_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        workspace_data = {
            'id': workspace_id,
            'name': name,
            'description': description,
            'created_at': timestamp,
            'updated_at': timestamp,
            'documents': [],  # List of document metadata
            'conversation_history': []  # List of conversation turns
        }

        # Create workspace directory
        workspace_dir = self._get_workspace_dir(workspace_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # Create documents subdirectory
        (workspace_dir / 'documents').mkdir(exist_ok=True)

        # Save workspace metadata
        self._save_workspace_metadata(workspace_id, workspace_data)

        return workspace_data

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workspace metadata.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Workspace metadata or None if not found
        """
        metadata_file = self._get_workspace_dir(workspace_id) / 'metadata.json'

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading workspace {workspace_id}: {e}")
            return None

    def update_workspace(self, workspace_id: str, name: Optional[str] = None,
                        description: Optional[str] = None) -> bool:
        """
        Update workspace metadata.

        Args:
            workspace_id: Workspace identifier
            name: New workspace name (optional)
            description: New workspace description (optional)

        Returns:
            True if successful, False otherwise
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        if name is not None:
            workspace['name'] = name
        if description is not None:
            workspace['description'] = description

        workspace['updated_at'] = datetime.utcnow().isoformat()

        self._save_workspace_metadata(workspace_id, workspace)
        return True

    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace and all its data.

        Args:
            workspace_id: Workspace identifier

        Returns:
            True if successful, False otherwise
        """
        workspace_dir = self._get_workspace_dir(workspace_id)

        if not workspace_dir.exists():
            return False

        try:
            shutil.rmtree(workspace_dir)
            return True
        except Exception as e:
            print(f"Error deleting workspace {workspace_id}: {e}")
            return False

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all workspaces.

        Returns:
            List of workspace metadata dictionaries
        """
        workspaces = []

        for workspace_dir in self.workspaces_path.iterdir():
            if workspace_dir.is_dir():
                metadata = self.get_workspace(workspace_dir.name)
                if metadata:
                    workspaces.append(metadata)

        # Sort by updated_at (most recent first)
        workspaces.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

        return workspaces

    def add_document_to_workspace(self, workspace_id: str, source_file: str,
                                  doc_metadata: Dict[str, Any]) -> Optional[str]:
        """
        Add a document to a workspace.

        Args:
            workspace_id: Workspace identifier
            source_file: Path to source document file
            doc_metadata: Document metadata

        Returns:
            Document ID if successful, None otherwise
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None

        doc_id = str(uuid.uuid4())
        source_path = Path(source_file)

        # Copy document to workspace documents directory
        dest_dir = self._get_workspace_dir(workspace_id) / 'documents'
        dest_file = dest_dir / f"{doc_id}_{source_path.name}"

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

        workspace['documents'].append(doc_entry)
        workspace['updated_at'] = datetime.utcnow().isoformat()

        self._save_workspace_metadata(workspace_id, workspace)

        return doc_id

    def remove_document_from_workspace(self, workspace_id: str, doc_id: str) -> bool:
        """
        Remove a document from a workspace.

        Args:
            workspace_id: Workspace identifier
            doc_id: Document identifier

        Returns:
            True if successful, False otherwise
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        # Find and remove document metadata
        doc_entry = None
        for i, doc in enumerate(workspace['documents']):
            if doc['id'] == doc_id:
                doc_entry = workspace['documents'].pop(i)
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

        workspace['updated_at'] = datetime.utcnow().isoformat()
        self._save_workspace_metadata(workspace_id, workspace)

        return True

    def get_workspace_documents(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents in a workspace.

        Args:
            workspace_id: Workspace identifier

        Returns:
            List of document metadata
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return []

        return workspace.get('documents', [])

    def add_conversation_turn(self, workspace_id: str, role: str, content: str,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a conversation turn to workspace history.

        Args:
            workspace_id: Workspace identifier
            role: Role (user/assistant)
            content: Message content
            metadata: Optional metadata (e.g., retrieved documents, sources)

        Returns:
            True if successful, False otherwise
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        turn = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        workspace['conversation_history'].append(turn)
        workspace['updated_at'] = datetime.utcnow().isoformat()

        self._save_workspace_metadata(workspace_id, workspace)

        return True

    def get_conversation_history(self, workspace_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a workspace.

        Args:
            workspace_id: Workspace identifier
            limit: Optional limit on number of turns to return (most recent)

        Returns:
            List of conversation turns
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return []

        history = workspace.get('conversation_history', [])

        if limit and limit > 0:
            return history[-limit:]

        return history

    def clear_conversation_history(self, workspace_id: str) -> bool:
        """
        Clear conversation history for a workspace.

        Args:
            workspace_id: Workspace identifier

        Returns:
            True if successful, False otherwise
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        workspace['conversation_history'] = []
        workspace['updated_at'] = datetime.utcnow().isoformat()

        self._save_workspace_metadata(workspace_id, workspace)

        return True

    def _get_workspace_dir(self, workspace_id: str) -> Path:
        """Get the directory path for a workspace."""
        return self.workspaces_path / workspace_id

    def _save_workspace_metadata(self, workspace_id: str, metadata: Dict[str, Any]):
        """Save workspace metadata to file."""
        metadata_file = self._get_workspace_dir(workspace_id) / 'metadata.json'

        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving workspace metadata: {e}")
            raise
