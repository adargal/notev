"""
Configuration management for Notev application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Storage Configuration
    BASE_DIR = Path(__file__).parent
    STORAGE_PATH = Path(os.getenv('STORAGE_PATH', BASE_DIR / 'storage'))
    GLOBAL_DOCS_PATH = Path(os.getenv('GLOBAL_DOCS_PATH', STORAGE_PATH / 'global_docs'))
    WORKSPACES_PATH = Path(os.getenv('WORKSPACES_PATH', STORAGE_PATH / 'workspaces'))

    # Document Processing Configuration
    CHUNK_SIZE = 1000  # Characters per chunk
    CHUNK_OVERLAP = 200  # Overlap between chunks

    # Claude Configuration
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
    EMBEDDING_MODEL = "voyage-3"  # Anthropic's embedding model
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7

    @classmethod
    def init_storage(cls):
        """Create storage directories if they don't exist."""
        cls.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        cls.GLOBAL_DOCS_PATH.mkdir(parents=True, exist_ok=True)
        cls.WORKSPACES_PATH.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Please set it in .env file or environment variables."
            )
