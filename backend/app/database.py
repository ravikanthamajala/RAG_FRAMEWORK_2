"""
Database connection module.

Provides the MongoDB database instance.
"""

from pymongo import MongoClient
import certifi
from config import Config

# Lazy MongoDB connection (non-blocking)
# Connection is established only when first used, not at import time
_client = None
_db = None

def get_db():
    """Get MongoDB database instance with lazy connection."""
    global _client, _db
    
    if _db is None:
        try:
            if 'mongodb+srv://' in Config.MONGO_URI or 'mongodb.net' in Config.MONGO_URI:
                # Atlas connection with CA bundle for TLS verification.
                _client = MongoClient(
                    Config.MONGO_URI,
                    serverSelectionTimeoutMS=5000,  # Reduced timeout for non-blocking startup
                    connectTimeoutMS=5000,
                    tls=True,
                    tlsCAFile=certifi.where(),
                    retryWrites=True,
                    w='majority'
                )
            else:
                # Local MongoDB - no SSL required
                _client = MongoClient(
                    Config.MONGO_URI,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
            
            _db = _client[Config.MONGO_DB_NAME]
            print("[OK] MongoDB connected successfully")
        except Exception as e:
            print(f"[WARNING] MongoDB connection failed: {e}")
            print("  Continuing with fallback mode...")
            # Return a mock db that won't crash the app
            return None
    
    return _db

# Backward compatibility - provide db as a property-like object
class DatabaseProxy:
    """Proxy to lazy-load database on access."""
    def __getitem__(self, key):
        db = get_db()
        if db is None:
            return None
        return db[key]
    
    def __getattr__(self, key):
        db = get_db()
        if db is None:
            return None
        return getattr(db, key)

db = DatabaseProxy()