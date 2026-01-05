"""
Configuration management for Notev application.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # Storage Configuration (defined first as other configs depend on it)
    BASE_DIR = Path(__file__).parent
    STORAGE_PATH = Path(os.getenv('STORAGE_PATH', BASE_DIR / 'storage'))
    GLOBAL_DOCS_PATH = Path(os.getenv('GLOBAL_DOCS_PATH', STORAGE_PATH / 'global_docs'))
    WORKSPACES_PATH = Path(os.getenv('WORKSPACES_PATH', STORAGE_PATH / 'workspaces'))
    CONFIG_FILE = STORAGE_PATH / 'config.json'

    # API Configuration - loaded from config file or environment
    ANTHROPIC_API_KEY = None
    VOYAGE_API_KEY = None

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

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
    def load_api_keys(cls):
        """Load API keys from config file, then fallback to environment variables."""
        # Try loading from config file first
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    cls.ANTHROPIC_API_KEY = config_data.get('anthropic_api_key') or None
                    cls.VOYAGE_API_KEY = config_data.get('voyage_api_key') or None
            except (json.JSONDecodeError, IOError):
                pass

        # Fallback to environment variables if not set from config file
        if not cls.ANTHROPIC_API_KEY:
            cls.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        if not cls.VOYAGE_API_KEY:
            cls.VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')

    @classmethod
    def save_api_keys(cls, anthropic_key=None, voyage_key=None):
        """Save API keys to config file."""
        # Ensure storage directory exists
        cls.STORAGE_PATH.mkdir(parents=True, exist_ok=True)

        # Load existing config or create new
        config_data = {}
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Update keys
        if anthropic_key is not None:
            config_data['anthropic_api_key'] = anthropic_key
            cls.ANTHROPIC_API_KEY = anthropic_key or None
        if voyage_key is not None:
            config_data['voyage_api_key'] = voyage_key
            cls.VOYAGE_API_KEY = voyage_key or None

        # Save to file
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)

    @classmethod
    def get_api_keys_status(cls):
        """Get status of API keys (configured or not, without revealing the keys)."""
        return {
            'anthropic_configured': bool(cls.ANTHROPIC_API_KEY),
            'voyage_configured': bool(cls.VOYAGE_API_KEY)
        }

    @classmethod
    def validate(cls):
        """Validate configuration. Returns True if valid, raises ValueError otherwise."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Please configure it in Settings."
            )

    @classmethod
    def is_configured(cls):
        """Check if minimum required configuration is present."""
        return bool(cls.ANTHROPIC_API_KEY)
