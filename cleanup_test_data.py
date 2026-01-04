#!/usr/bin/env python
"""
Cleanup script to remove test workspaces created by unit tests.
Run this if you see test events appearing in the UI.
"""
from pathlib import Path
import shutil
from config import Config

def cleanup_test_workspaces():
    """Remove workspaces with test-related names."""
    Config.init_storage()
    workspaces_path = Config.WORKSPACES_PATH

    if not workspaces_path.exists():
        print("No workspaces directory found.")
        return

    test_keywords = ['test', 'Test', 'delete', 'Delete', 'Get Test', 'Chat Test',
                     'History Test', 'Clear Test', 'stats_test', 'search_test']

    removed_count = 0

    # Read all workspace metadata files
    for workspace_dir in workspaces_path.iterdir():
        if not workspace_dir.is_dir():
            continue

        metadata_file = workspace_dir / 'metadata.json'
        if not metadata_file.exists():
            continue

        try:
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            workspace_name = metadata.get('name', '')

            # Check if workspace name contains test keywords
            if any(keyword in workspace_name for keyword in test_keywords):
                print(f"Removing test workspace: {workspace_name} (ID: {workspace_dir.name})")
                shutil.rmtree(workspace_dir)
                removed_count += 1

        except Exception as e:
            print(f"Error processing {workspace_dir.name}: {e}")

    print(f"\nRemoved {removed_count} test workspace(s).")

if __name__ == '__main__':
    print("Cleaning up test workspaces...\n")
    cleanup_test_workspaces()
    print("\nDone! Refresh your browser to see the updated workspace list.")
