"""
Notev Launcher
Launches the Flask server and opens the browser automatically.
"""
import sys
import os
import webbrowser
import threading
import time
import socket
import traceback

# PyInstaller hidden imports - these must be imported at module level
# so PyInstaller can detect and bundle them
import flask
import flask_cors
import werkzeug
import jinja2
import markupsafe
import click
import itsdangerous
import blinker
import anthropic
import httpx
import dotenv
import docx
import pptx
import pypdf
import numpy
try:
    import voyageai
except ImportError:
    pass  # Optional dependency

# Ensure we're running from the correct directory
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    BASE_DIR = os.path.dirname(sys.executable)
    # PyInstaller extracts to a temp folder, get the real path
    if hasattr(sys, '_MEIPASS'):
        BUNDLE_DIR = sys._MEIPASS
    else:
        BUNDLE_DIR = BASE_DIR
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

os.chdir(BASE_DIR)

# Add both directories to path for imports
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, BUNDLE_DIR)


def find_free_port(start_port=5000, max_attempts=100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start_port  # Fallback to default


def open_browser(port, delay=1.5):
    """Open browser after a short delay to let the server start."""
    time.sleep(delay)
    url = f'http://127.0.0.1:{port}'
    print(f"\nOpening browser at {url}")
    webbrowser.open(url)


def main():
    """Main entry point for the launcher."""
    print("=" * 60)
    print("  NOTEV - AI-Powered Operations Decision Support")
    print("=" * 60)
    print()

    # Find a free port
    port = find_free_port(5000)
    print(f"Starting server on port {port}...")

    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()

    # Import and run the Flask app
    from app import app

    print("\nServer is running. Press Ctrl+C to stop.")
    print(f"If browser doesn't open, visit: http://127.0.0.1:{port}")
    print()

    # Run Flask app (blocking)
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        use_reloader=False
    )


if __name__ == '__main__':
    main()
