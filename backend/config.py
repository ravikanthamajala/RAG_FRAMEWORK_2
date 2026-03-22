"""
Configuration settings for the Flask application.

Loads environment variables and defines configuration classes.
"""

# Import necessary modules
import os
from pathlib import Path
from dotenv import load_dotenv

# Fix for Pandas/NumPy hanging on Windows due to MKL initialization.
# Must be done BEFORE any import of pandas, numpy, or dependent libraries.
os.environ.setdefault('NUMEXPR_MAX_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

# Load environment variables from backend/.env and project-root/.env.
# Existing OS environment variables keep precedence.
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / '.env')
load_dotenv(PROJECT_ROOT / '.env')

class Config:
    """
    Configuration class for the application.

    Contains settings loaded from environment variables with defaults.
    """

    # Secret key for Flask sessions
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

    # MongoDB connection settings
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/agentic_rag')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'agentic_rag')

    # Base URL for Ollama API
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

    # Language model to use
    LLM_MODEL = os.getenv('LLM_MODEL', 'mistral:7b')

    # Embedding model for vectorization
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')

    # Folder for uploaded files
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    # Maximum content length for uploads (500MB for automotive market data)
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB