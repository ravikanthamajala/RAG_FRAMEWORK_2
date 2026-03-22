"""
Document model for interacting with MongoDB documents collection.

Provides methods for inserting, finding, and vector searching documents.
"""

from app.database import db


class Document:
    """
    Model class for document operations in MongoDB.
    """

    @staticmethod
    def _get_collection():
        """Resolve the Mongo collection lazily so imports do not trigger DB access."""
        collection = db.documents
        if collection is None:
            raise RuntimeError('MongoDB is not available')
        return collection

    @staticmethod
    def insert_document(doc_data):
        """
        Insert a new document into the collection.

        Args:
            doc_data (dict): The document data to insert.

        Returns:
            InsertOneResult: The result of the insert operation.
        """
        return Document._get_collection().insert_one(doc_data)

    @staticmethod
    def find_documents(query):
        """
        Find documents matching the query.

        Args:
            query (dict): The query filter.

        Returns:
            list: List of matching documents.
        """
        return list(Document._get_collection().find(query))

    @staticmethod
    def vector_search(embedding, limit=5):
        """
        Perform vector search on the documents.

        Args:
            embedding (list): The query embedding vector.
            limit (int): Maximum number of results to return.

        Returns:
            list: List of documents from vector search.
        """
        # Assuming MongoDB Atlas vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": 100,
                    "limit": limit
                }
            }
        ]
        return list(Document._get_collection().aggregate(pipeline))