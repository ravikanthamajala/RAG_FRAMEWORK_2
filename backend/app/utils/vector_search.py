"""
Vector search utilities.

Provides functions to search for similar documents using embeddings.
"""

from app.models.document import Document
from app.utils.embeddings import generate_embedding, cosine_similarity
import numpy as np

def search_similar_documents(query_embedding, top_k=5):
    """
    Search for documents similar to the query embedding.

    Args:
        query_embedding (list): The query embedding vector.
        top_k (int): Number of top similar documents to return.

    Returns:
        list: List of similar documents.
    """
    # For local search if MongoDB vector search not available
    # Fetch all documents
    documents = Document.find_documents({})
    # Calculate similarities
    similarities = []
    for doc in documents:
        if 'embedding' in doc:
            sim = cosine_similarity(query_embedding, doc['embedding'])
            similarities.append((doc, sim))
    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    # Return top k documents, injecting the similarity score into each doc dict
    results = []
    for doc, sim in similarities[:top_k]:
        if isinstance(doc, dict):
            doc = dict(doc)          # shallow copy — avoid mutating cached/shared dicts
            doc['score'] = float(sim)
        results.append(doc)
    return results