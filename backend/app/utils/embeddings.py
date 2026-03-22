"""
Embedding utilities using Ollama.

Provides functions to generate embeddings and calculate similarity.
"""

from langchain_ollama import OllamaEmbeddings
import numpy as np
import os

# nomic-embed-text supports 8192 tokens; keep well under to avoid 400 errors.
# ~4 chars per token → 20 000 chars ≈ 5 000 tokens
_EMBED_MAX_CHARS = 20_000

# Module-level singleton — reuse one instance instead of creating a new one
# on every generate_embedding() call, which was causing memory exhaustion.
_embeddings_instance = None


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> list:
    """
    Split *text* into overlapping chunks of approximately *chunk_size* characters.
    Tries to break at sentence / paragraph boundaries for semantic coherence.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to end at a natural boundary in the second half of the window
        if end < len(text):
            for sep in ['\n\n', '.\n', '. ', '\n', ' ']:
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break

    return chunks or [text]


def get_embeddings():
    """
    Return the shared Ollama embeddings instance (created once, reused always).
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = OllamaEmbeddings(
            model=os.getenv('EMBEDDING_MODEL', 'nomic-embed-text'),
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        )
    return _embeddings_instance

def generate_embedding(text):
    """
    Generate embedding for a given text.

    Args:
        text (str): The text to embed.

    Returns:
        list: The embedding vector.
    """
    # Safety truncation: never send more than _EMBED_MAX_CHARS to the model
    if len(text) > _EMBED_MAX_CHARS:
        text = text[:_EMBED_MAX_CHARS]
    # Get embeddings instance
    embeddings = get_embeddings()
    # Embed the query
    return embeddings.embed_query(text)

def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two vectors.

    Args:
        a (list): First vector.
        b (list): Second vector.

    Returns:
        float: Cosine similarity score.
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))