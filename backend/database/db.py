"""
Database connection and management for MongoDB
"""
import os
import sys
from typing import Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MongoDB database connections and operations
    """
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connected = False
        
        # Load configuration
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("MONGO_DB_NAME", "amdox_db")
        
        logger.info(f"Database manager initialized with URI: {self.mongo_uri}")
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self._connected:
                logger.warning("Already connected to database")
                return True
            
            logger.info(f"Connecting to MongoDB: {self.mongo_uri}")
            
            # Create client with proper options
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Verify connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[self.db_name]
            self._connected = True
            
            logger.info(f"✅ Connected to MongoDB database: {self.db_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self._connected = False
            return False
    
    def close_connection(self):
        """
        Close the database connection properly
        """
        try:
            if self.client:
                self.client.close()
                logger.info("✅ Database connection closed properly")
            self._connected = False
            self.client = None
            self.db = None
        except Exception as e:
            logger.error(f"❌ Error closing database connection: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if database is connected
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected and self.client is not None
    
    def get_database(self) -> Optional[Database]:
        """
        Get the database instance
        
        Returns:
            Database: MongoDB database instance or None
        """
        return self.db
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """
        Get a collection by name
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Collection: MongoDB collection or None
        """
        if self.db is None:
            logger.error("Database not connected")
            return None
        
        return self.db[collection_name]
    
    def health_check(self) -> dict:
        """
        Check database health
        
        Returns:
            dict: Health status information
        """
        result = {
            "status": "unknown",
            "database": self.db_name if self.db else None,
            "connected": self._connected,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if self._connected and self.client:
                # Test connection
                self.client.admin.command('ping')
                
                # Get collection count
                collections = self.db.list_collection_names()
                result["status"] = "healthy"
                result["collections_count"] = len(collections)
                result["collections"] = collections
                
            else:
                result["status"] = "disconnected"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def create_indexes(self, collection_name: str, indexes: list):
        """
        Create indexes for a collection
        
        Args:
            collection_name: Name of the collection
            indexes: List of index specifications
        """
        try:
            collection = self.get_collection(collection_name)
            if collection:
                for index in indexes:
                    collection.create_index(index)
                logger.info(f"✅ Created {len(indexes)} indexes for {collection_name}")
        except Exception as e:
            logger.error(f"❌ Error creating indexes for {collection_name}: {e}")
    
    def drop_collection(self, collection_name: str) -> bool:
        """
        Drop a collection (use with caution)
        
        Args:
            collection_name: Name of the collection to drop
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.db:
                self.db.drop_collection(collection_name)
                logger.info(f"✅ Dropped collection: {collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error dropping collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> list:
        """
        List all collections in the database
        
        Returns:
            list: List of collection names
        """
        try:
            if self.db:
                return self.db.list_collection_names()
            return []
        except Exception as e:
            logger.error(f"❌ Error listing collections: {e}")
            return []


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance
    
    Returns:
        DatabaseManager: The database manager instance
    """
    return db_manager


def init_db():
    """
    Initialize the database connection
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    return db_manager.connect()


def close_db():
    """
    Close the database connection
    """
    db_manager.close_connection()


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    
    if db_manager.connect():
        print("✅ Database connection successful")
        print(f"Database: {db_manager.db.name}")
        
        # List collections
        collections = db_manager.list_collections()
        print(f"Collections: {collections}")
        
        # Health check
        health = db_manager.health_check()
        print(f"Health: {health}")
        
        # Close connection
        db_manager.close_connection()
    else:
        print("❌ Database connection failed")
        sys.exit(1)

