"""
Unit tests for workspace manager module.
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from notev_backend.modules.workspace_manager import WorkspaceManager


class TestWorkspaceManager(unittest.TestCase):
    """Test cases for WorkspaceManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test workspaces
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = WorkspaceManager(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_create_workspace(self):
        """Test creating a new workspace."""
        workspace = self.manager.create_workspace(
            name="Test Workspace",
            description="Test description"
        )

        self.assertIsNotNone(workspace)
        self.assertEqual(workspace['name'], "Test Workspace")
        self.assertEqual(workspace['description'], "Test description")
        self.assertIn('id', workspace)
        self.assertIn('created_at', workspace)

    def test_get_workspace(self):
        """Test retrieving a workspace."""
        created = self.manager.create_workspace("Test", "Description")
        workspace_id = created['id']

        retrieved = self.manager.get_workspace(workspace_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['id'], workspace_id)
        self.assertEqual(retrieved['name'], "Test")

    def test_get_nonexistent_workspace(self):
        """Test retrieving a non-existent workspace."""
        workspace = self.manager.get_workspace("nonexistent-id")
        self.assertIsNone(workspace)

    def test_update_workspace(self):
        """Test updating workspace metadata."""
        workspace = self.manager.create_workspace("Original", "Original desc")
        workspace_id = workspace['id']

        success = self.manager.update_workspace(
            workspace_id,
            name="Updated",
            description="Updated desc"
        )

        self.assertTrue(success)

        updated = self.manager.get_workspace(workspace_id)
        self.assertEqual(updated['name'], "Updated")
        self.assertEqual(updated['description'], "Updated desc")

    def test_delete_workspace(self):
        """Test deleting a workspace."""
        workspace = self.manager.create_workspace("To Delete", "")
        workspace_id = workspace['id']

        success = self.manager.delete_workspace(workspace_id)
        self.assertTrue(success)

        # Verify it's gone
        retrieved = self.manager.get_workspace(workspace_id)
        self.assertIsNone(retrieved)

    def test_list_workspaces(self):
        """Test listing all workspaces."""
        self.manager.create_workspace("Workspace 1", "")
        self.manager.create_workspace("Workspace 2", "")

        workspaces = self.manager.list_workspaces()

        self.assertEqual(len(workspaces), 2)
        names = [w['name'] for w in workspaces]
        self.assertIn("Workspace 1", names)
        self.assertIn("Workspace 2", names)

    def test_add_conversation_turn(self):
        """Test adding a conversation turn."""
        workspace = self.manager.create_workspace("Chat Test", "")
        workspace_id = workspace['id']

        success = self.manager.add_conversation_turn(
            workspace_id,
            role="user",
            content="Hello, AI!"
        )

        self.assertTrue(success)

        history = self.manager.get_conversation_history(workspace_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['role'], "user")
        self.assertEqual(history[0]['content'], "Hello, AI!")

    def test_get_conversation_history_with_limit(self):
        """Test getting conversation history with limit."""
        workspace = self.manager.create_workspace("History Test", "")
        workspace_id = workspace['id']

        # Add multiple turns
        for i in range(5):
            self.manager.add_conversation_turn(
                workspace_id,
                role="user",
                content=f"Message {i}"
            )

        # Get last 3
        history = self.manager.get_conversation_history(workspace_id, limit=3)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[-1]['content'], "Message 4")

    def test_clear_conversation_history(self):
        """Test clearing conversation history."""
        workspace = self.manager.create_workspace("Clear Test", "")
        workspace_id = workspace['id']

        self.manager.add_conversation_turn(workspace_id, "user", "Test")
        self.manager.clear_conversation_history(workspace_id)

        history = self.manager.get_conversation_history(workspace_id)
        self.assertEqual(len(history), 0)


if __name__ == '__main__':
    unittest.main()
