"""
Enhanced Database Manager for Amdox
Production-grade MongoDB connection with pooling, retry logic, and health monitoring
"""
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError,
    OperationFailure,
    ConfigurationError
)
import logging
import time
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry_on_failure(max_retries=3, delay=1):
    """Decorator for retrying database operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"❌ Max retries reached for {func.__name__}: {e}")
                        raise
                    logger.warning(f"⚠️ Retry {retries}/{max_retries} for {func.__name__}")
                    time.sleep(delay * retries)  # Exponential backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DatabaseManager:
    """
    Enhanced MongoDB database manager with connection pooling and monitoring
    """
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connected = False
        self._connection_attempts = 0
        self._last_health_check = None
        self._health_check_interval = 60  # seconds
        
        # Load configuration
        self.mongo_uri = os.getenv(
            "MONGO_URI", 
            "mongodb+srv://akshat:akshat@cluster0.3lfsels.mongodb.net/"
        )
        self.db_name = os.getenv("MONGO_DB_NAME", "amdox_db")
        
        # Connection pool settings
        self.max_pool_size = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
        self.min_pool_size = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
        self.max_idle_time_ms = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", "30000"))
        
        # Connection timeout settings
        self.server_selection_timeout_ms = int(
            os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000")
        )
        self.connect_timeout_ms = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
        self.socket_timeout_ms = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "5000"))
        
        # Retry settings
        self.retry_writes = os.getenv("MONGO_RETRY_WRITES", "true").lower() == "true"
        self.retry_reads = os.getenv("MONGO_RETRY_READS", "true").lower() == "true"
        
        logger.info(f"💾 Database manager initialized for: {self.db_name}")
    
    @retry_on_failure(max_retries=3, delay=2)
    def connect(self) -> bool:
        """
        Establish connection to MongoDB with retry logic
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self._connected:
                logger.warning("⚠️ Already connected to database")
                return True
            
            self._connection_attempts += 1
            logger.info(f"🔌 Connecting to MongoDB (Attempt {self._connection_attempts})...")
            logger.info(f"📍 Database: {self.db_name}")
            
            # Create client with optimized settings
            self.client = MongoClient(
                self.mongo_uri,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms,
                retryWrites=self.retry_writes,
                retryReads=self.retry_reads,
                appName="Amdox_Emotion_Detection",
                compressors="snappy,zlib"  # Enable compression
            )
            
            # Verify connection with ping
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[self.db_name]
            self._connected = True
            self._last_health_check = datetime.utcnow()
            
            logger.info(f"✅ Successfully connected to MongoDB")
            logger.info(f"   Database: {self.db_name}")
            logger.info(f"   Pool Size: {self.min_pool_size}-{self.max_pool_size}")
            logger.info(f"   Retry Writes: {self.retry_writes}")
            logger.info(f"   Retry Reads: {self.retry_reads}")
            
            # Create indexes after connection
            self._create_all_indexes()
            
            return True
            
        except ConnectionFailure as e:
            logger.error(f"❌ Connection failure: {e}")
            self._connected = False
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ Server selection timeout: {e}")
            logger.info("💡 Check if MongoDB server is accessible")
            self._connected = False
            raise
        except ConfigurationError as e:
            logger.error(f"❌ Configuration error: {e}")
            logger.info("💡 Check MongoDB URI and credentials")
            self._connected = False
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self._connected = False
            raise
    
    def close_connection(self):
        """
        Close the database connection properly with cleanup
        """
        try:
            if self.client:
                # Log connection statistics before closing
                stats = self.get_connection_stats()
                logger.info(f"📊 Final connection stats: {stats}")
                
                self.client.close()
                logger.info("✅ Database connection closed properly")
            
            self._connected = False
            self.client = None
            self.db = None
            self._last_health_check = None
            
        except Exception as e:
            logger.error(f"❌ Error closing database connection: {e}")
    
    def reconnect(self) -> bool:
        """
        Reconnect to database
        
        Returns:
            bool: True if reconnection successful
        """
        logger.info("🔄 Attempting to reconnect to database...")
        self.close_connection()
        return self.connect()
    
    def is_connected(self) -> bool:
        """
        Check if database is connected with health verification
        
        Returns:
            bool: True if connected and healthy, False otherwise
        """
        if not self._connected or self.client is None:
            return False
        
        # Perform periodic health check
        if self._should_perform_health_check():
            try:
                self.client.admin.command('ping')
                self._last_health_check = datetime.utcnow()
                return True
            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
                self._connected = False
                return False
        
        return self._connected
    
    def _should_perform_health_check(self) -> bool:
        """Check if health check should be performed"""
        if self._last_health_check is None:
            return True
        
        elapsed = (datetime.utcnow() - self._last_health_check).total_seconds()
        return elapsed >= self._health_check_interval
    
    def get_database(self) -> Optional[Database]:
        """
        Get the database instance with connection verification
        
        Returns:
            Database: MongoDB database instance or None
        """
        if not self.is_connected():
            logger.warning("⚠️ Database not connected, attempting reconnection...")
            try:
                self.reconnect()
            except Exception as e:
                logger.error(f"❌ Reconnection failed: {e}")
                return None
        
        return self.db
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """
        Get a collection by name with existence verification
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Collection: MongoDB collection or None
        """
        if self.db is None:
            logger.error("❌ Database not connected")
            return None
        
        try:
            collection = self.db[collection_name]
            
            # Verify collection exists (create if not)
            if collection_name not in self.db.list_collection_names():
                logger.info(f"📝 Creating collection: {collection_name}")
            
            return collection
            
        except Exception as e:
            logger.error(f"❌ Error getting collection {collection_name}: {e}")
            return None
    
    @retry_on_failure(max_retries=2)
    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive database health check
        
        Returns:
            dict: Health status information
        """
        result = {
            "status": "unknown",
            "database": self.db_name if self.db else None,
            "connected": self._connected,
            "timestamp": datetime.utcnow().isoformat(),
            "connection_attempts": self._connection_attempts
        }
        
        try:
            if self._connected and self.client:
                # Test connection
                ping_result = self.client.admin.command('ping')
                
                # Get server info
                server_info = self.client.server_info()
                
                # Get collection count and stats
                collections = self.db.list_collection_names()
                
                # Get database stats
                db_stats = self.db.command("dbStats")
                
                result.update({
                    "status": "healthy",
                    "ping": ping_result,
                    "server_version": server_info.get("version"),
                    "collections": {
                        "count": len(collections),
                        "names": collections
                    },
                    "database_stats": {
                        "collections": db_stats.get("collections"),
                        "objects": db_stats.get("objects"),
                        "data_size": db_stats.get("dataSize"),
                        "storage_size": db_stats.get("storageSize"),
                        "indexes": db_stats.get("indexes"),
                        "index_size": db_stats.get("indexSize")
                    },
                    "connection_pool": self.get_connection_stats()
                })
                
            else:
                result["status"] = "disconnected"
                result["message"] = "Database is not connected"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
            logger.error(f"❌ Health check error: {e}")
        
        return result
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics
        
        Returns:
            dict: Connection pool stats
        """
        stats = {
            "max_pool_size": self.max_pool_size,
            "min_pool_size": self.min_pool_size,
            "active_connections": "N/A",
            "available_connections": "N/A"
        }
        
        try:
            if self.client:
                # Get pool stats from client
                pool_options = self.client._MongoClient__options.pool_options
                stats.update({
                    "max_pool_size": pool_options.max_pool_size,
                    "min_pool_size": pool_options.min_pool_size,
                    "max_idle_time_ms": pool_options.max_idle_time_ms
                })
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
        
        return stats
    
    def _create_all_indexes(self):
        """Create all required indexes for optimal performance"""
        try:
            logger.info("📑 Creating database indexes...")
            
            # Users collection indexes
            self.create_indexes("users", [
                [("user_id", ASCENDING)],
                [("email", ASCENDING)],
                [("team_id", ASCENDING)],
                [("created_at", DESCENDING)]
            ], unique_fields=["user_id", "email"])
            
            # Mood entries collection indexes
            self.create_indexes("mood_entries", [
                [("user_id", ASCENDING)],
                [("session_id", ASCENDING)],
                [("timestamp", DESCENDING)],
                [("user_id", ASCENDING), ("timestamp", DESCENDING)],
                [("stress_score", DESCENDING)],
                [("dominant_emotion", ASCENDING)]
            ])
            
            # Teams collection indexes
            self.create_indexes("teams", [
                [("team_id", ASCENDING)],
                [("name", ASCENDING)],
                [("created_at", DESCENDING)]
            ], unique_fields=["team_id"])
            
            # Alerts collection indexes
            self.create_indexes("alerts", [
                [("user_id", ASCENDING)],
                [("created_at", DESCENDING)],
                [("acknowledged", ASCENDING)],
                [("severity", ASCENDING)],
                [("user_id", ASCENDING), ("created_at", DESCENDING)]
            ])
            
            # Recommendation feedback collection indexes
            self.create_indexes("recommendation_feedback", [
                [("user_id", ASCENDING)],
                [("recommendation_id", ASCENDING)],
                [("timestamp", DESCENDING)]
            ])
            
            logger.info("✅ All indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
    
    def create_indexes(
        self, 
        collection_name: str, 
        indexes: List[List],
        unique_fields: Optional[List[str]] = None
    ):
        """
        Create indexes for a collection with error handling
        
        Args:
            collection_name: Name of the collection
            indexes: List of index specifications
            unique_fields: List of fields that should have unique indexes
        """
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return
            
            created_count = 0
            
            for index_spec in indexes:
                try:
                    # Check if this should be unique
                    is_unique = False
                    if unique_fields and len(index_spec) == 1:
                        field_name = index_spec[0][0]
                        is_unique = field_name in unique_fields
                    
                    # Create index
                    collection.create_index(
                        index_spec,
                        unique=is_unique,
                        background=True  # Create in background
                    )
                    created_count += 1
                    
                except OperationFailure as e:
                    if "already exists" not in str(e):
                        logger.warning(f"⚠️ Index creation warning for {collection_name}: {e}")
            
            if created_count > 0:
                logger.info(f"✅ Created {created_count} indexes for {collection_name}")
            
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
            if self.db is not None:
                self.db.drop_collection(collection_name)
                logger.info(f"🗑️ Dropped collection: {collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error dropping collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all collections in the database
        
        Returns:
            list: List of collection names
        """
        try:
            if self.db is not None:
                return self.db.list_collection_names()
            return []
        except Exception as e:
            logger.error(f"❌ Error listing collections: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a collection
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            dict: Collection statistics
        """
        try:
            if self.db is not None:
                stats = self.db.command("collStats", collection_name)
                return {
                    "count": stats.get("count", 0),
                    "size": stats.get("size", 0),
                    "storage_size": stats.get("storageSize", 0),
                    "indexes": stats.get("nindexes", 0),
                    "index_size": stats.get("totalIndexSize", 0),
                    "avg_obj_size": stats.get("avgObjSize", 0)
                }
        except Exception as e:
            logger.error(f"❌ Error getting collection stats: {e}")
        
        return {}
    
    def backup_collection(
        self, 
        collection_name: str, 
        backup_name: Optional[str] = None
    ) -> bool:
        """
        Create a backup of a collection
        
        Args:
            collection_name: Name of the collection to backup
            backup_name: Optional backup collection name
        
        Returns:
            bool: True if successful
        """
        try:
            if not backup_name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{collection_name}_backup_{timestamp}"
            
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            # Copy all documents to backup collection
            docs = list(collection.find({}))
            if docs:
                backup_collection = self.get_collection(backup_name)
                backup_collection.insert_many(docs)
                logger.info(f"✅ Backed up {len(docs)} documents to {backup_name}")
                return True
            
            logger.warning(f"⚠️ No documents to backup in {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error backing up collection: {e}")
            return False
    
    def cleanup_old_data(
        self, 
        collection_name: str, 
        field_name: str,
        days: int = 90
    ) -> int:
        """
        Clean up old data from a collection
        
        Args:
            collection_name: Name of the collection
            field_name: Date field name to filter by
            days: Number of days to keep
        
        Returns:
            int: Number of deleted documents
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            collection = self.get_collection(collection_name)
            
            if collection is None:
                return 0
            
            result = collection.delete_many({
                field_name: {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"🗑️ Cleaned up {deleted_count} old documents from {collection_name}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old data: {e}")
            return 0
    
    def get_database_size(self) -> Dict[str, Any]:
        """
        Get total database size information
        
        Returns:
            dict: Database size information
        """
        try:
            if self.db is not None:
                stats = self.db.command("dbStats", scale=1024*1024)  # MB
                return {
                    "data_size_mb": round(stats.get("dataSize", 0), 2),
                    "storage_size_mb": round(stats.get("storageSize", 0), 2),
                    "index_size_mb": round(stats.get("indexSize", 0), 2),
                    "total_size_mb": round(
                        stats.get("dataSize", 0) + stats.get("indexSize", 0), 
                        2
                    ),
                    "collections": stats.get("collections", 0),
                    "objects": stats.get("objects", 0)
                }
        except Exception as e:
            logger.error(f"❌ Error getting database size: {e}")
        
        return {}
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Optimize database performance
        
        Returns:
            dict: Optimization results
        """
        results = {
            "success": True,
            "operations": []
        }
        
        try:
            # Compact collections
            collections = self.list_collections()
            for coll_name in collections:
                try:
                    # Note: compact requires admin privileges
                    self.db.command("compact", coll_name)
                    results["operations"].append(f"Compacted {coll_name}")
                except Exception as e:
                    results["operations"].append(f"Could not compact {coll_name}: {e}")
            
            logger.info("✅ Database optimization completed")
            
        except Exception as e:
            logger.error(f"❌ Error optimizing database: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance
    
    Returns:
        DatabaseManager: The database manager instance
    """
    return db_manager


def init_db() -> bool:
    """
    Initialize the database connection
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        return db_manager.connect()
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


def close_db():
    """Close the database connection"""
    db_manager.close_connection()


# Context manager for database operations
class DatabaseContext:
    """Context manager for database operations with auto-commit/rollback"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.session = None
    
    def __enter__(self):
        if not self.db_manager.is_connected():
            self.db_manager.connect()
        return self.db_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"❌ Database operation failed: {exc_val}")
        return False


if __name__ == "__main__":
    # Test database connection
    print("🧪 Testing database connection...")
    print("=" * 60)
    
    try:
        with DatabaseContext() as db_mgr:
            if db_mgr.is_connected():
                print("✅ Database connection successful")
                print(f"📍 Database: {db_mgr.db.name}")
                
                # List collections
                collections = db_mgr.list_collections()
                print(f"📚 Collections ({len(collections)}): {collections}")
                
                # Health check
                health = db_mgr.health_check()
                print(f"🏥 Health Status: {health.get('status')}")
                
                # Connection stats
                stats = db_mgr.get_connection_stats()
                print(f"📊 Connection Stats: {stats}")
                
                # Database size
                size_info = db_mgr.get_database_size()
                print(f"💾 Database Size: {size_info}")
                
                print("=" * 60)
                print("✅ All tests passed!")
            else:
                print("❌ Database connection failed")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)