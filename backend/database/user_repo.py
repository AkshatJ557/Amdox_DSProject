"""
Enhanced User Repository for Amdox
Production-grade user management with authentication and profile tracking
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager


class UserRepository:
    """
    Enhanced repository for user-related database operations
    """
    
    def __init__(self):
        self.collection_name = "users"
        self._collection = None
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        logger.info("👤 User Repository initialized")
    
    @property
    def collection(self):
        """Get the users collection with lazy loading"""
        if self._collection is None:
            self._collection = db_manager.get_collection(self.collection_name)
        return self._collection
    
    def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user with validation
        
        Args:
            user_data: User information dictionary
        
        Returns:
            dict: Created user document
        """
        try:
            # Validate required fields
            required_fields = ["user_id", "name", "email"]
            for field in required_fields:
                if field not in user_data:
                    logger.error(f"❌ Missing required field: {field}")
                    return {"error": f"Missing required field: {field}"}
            
            # Validate email format
            if "@" not in user_data["email"]:
                return {"error": "Invalid email format"}
            
            # Add timestamps and metadata
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            user_data["last_login"] = None
            user_data["active"] = user_data.get("active", True)
            user_data["role"] = user_data.get("role", "employee")
            
            # Hash password if provided
            if "password" in user_data:
                user_data["password_hash"] = self._hash_password(user_data["password"])
                del user_data["password"]  # Remove plain password
            
            # Add metadata
            user_data["_metadata"] = {
                "created_by": "system",
                "version": "1.0",
                "login_count": 0
            }
            
            result = self.collection.insert_one(user_data)
            user_data["_id"] = str(result.inserted_id)
            
            logger.info(f"✅ User created: {user_data['user_id']} ({user_data['name']})")
            
            # Clear cache
            self.clear_all_cache()
            
            # Remove password hash from return
            if "password_hash" in user_data:
                del user_data["password_hash"]
            
            return user_data
            
        except DuplicateKeyError as e:
            logger.error(f"❌ Duplicate user_id or email: {e}")
            return {"error": "User ID or email already exists"}
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            return {"error": str(e)}
    
    def get_user_by_id(self, user_id: str, include_sensitive: bool = False) -> Optional[Dict]:
        """
        Get user by user_id with caching
        
        Args:
            user_id: The user ID
            include_sensitive: Include password hash
        
        Returns:
            dict: User document or None
        """
        try:
            # Check cache
            cache_key = f"user_{user_id}"
            cached = self._get_cached(cache_key)
            if cached and not include_sensitive:
                return cached
            
            user = self.collection.find_one({"user_id": user_id})
            
            if user:
                user["_id"] = str(user["_id"])
                
                # Remove sensitive data unless requested
                if not include_sensitive and "password_hash" in user:
                    user_copy = user.copy()
                    del user_copy["password_hash"]
                    self._set_cache(cache_key, user_copy)
                    return user_copy
                
                if not include_sensitive and "password_hash" in user:
                    del user["password_hash"]
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email
        
        Args:
            email: User email address
        
        Returns:
            dict: User document or None
        """
        try:
            user = self.collection.find_one({"email": email.lower()})
            
            if user:
                user["_id"] = str(user["_id"])
                if "password_hash" in user:
                    del user["password_hash"]
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Error getting user by email: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: Plain text password
        
        Returns:
            dict: User document if authenticated, None otherwise
        """
        try:
            user = self.collection.find_one({"email": email.lower()})
            
            if not user:
                logger.warning(f"⚠️ Authentication failed: User not found for {email}")
                return None
            
            # Check if user is active
            if not user.get("active", True):
                logger.warning(f"⚠️ Authentication failed: Inactive user {email}")
                return None
            
            # Verify password
            if "password_hash" in user:
                password_hash = self._hash_password(password)
                if user["password_hash"] != password_hash:
                    logger.warning(f"⚠️ Authentication failed: Invalid password for {email}")
                    return None
            
            # Update last login and login count
            self.collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {"last_login": datetime.utcnow()},
                    "$inc": {"_metadata.login_count": 1}
                }
            )
            
            # Remove sensitive data
            user["_id"] = str(user["_id"])
            if "password_hash" in user:
                del user["password_hash"]
            
            logger.info(f"✅ User authenticated: {user['user_id']}")
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Error authenticating user: {e}")
            return None
    
    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """
        Update user information
        
        Args:
            user_id: The user ID
            update_data: Fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Hash password if being updated
            if "password" in update_data:
                update_data["password_hash"] = self._hash_password(update_data["password"])
                del update_data["password"]
            
            # Validate email if being updated
            if "email" in update_data:
                if "@" not in update_data["email"]:
                    logger.error("❌ Invalid email format")
                    return False
                update_data["email"] = update_data["email"].lower()
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ User updated: {user_id}")
                self._clear_cache(f"user_{user_id}")
                self.clear_all_cache()
            
            return result.modified_count > 0
            
        except DuplicateKeyError:
            logger.error("❌ Email already exists")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a user (soft or hard delete)
        
        Args:
            user_id: The user ID
            hard_delete: Permanently delete (vs soft delete)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if hard_delete:
                result = self.collection.delete_one({"user_id": user_id})
                if result.deleted_count > 0:
                    logger.warning(f"⚠️ User permanently deleted: {user_id}")
            else:
                # Soft delete
                result = self.collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "active": False,
                            "deleted_at": datetime.utcnow()
                        }
                    }
                )
                if result.modified_count > 0:
                    logger.info(f"🗑️ User soft-deleted: {user_id}")
            
            self._clear_cache(f"user_{user_id}")
            self.clear_all_cache()
            
            return (result.deleted_count if hard_delete else result.modified_count) > 0
            
        except Exception as e:
            logger.error(f"❌ Error deleting user: {e}")
            return False
    
    def get_all_users(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all users with pagination and filtering
        
        Args:
            include_inactive: Include inactive users
            skip: Number to skip
            limit: Maximum to return
            role: Filter by role
        
        Returns:
            list: List of user documents
        """
        try:
            query = {}
            if not include_inactive:
                query["active"] = {"$ne": False}
            if role:
                query["role"] = role
            
            users = list(
                self.collection
                .find(query, {"password_hash": 0})  # Exclude password
                .skip(skip)
                .limit(limit)
                .sort("created_at", -1)
            )
            
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error getting all users: {e}")
            return []
    
    def get_users_by_team(self, team_id: str) -> List[Dict]:
        """
        Get all users in a team
        
        Args:
            team_id: The team ID
        
        Returns:
            list: List of user documents
        """
        try:
            users = list(
                self.collection.find(
                    {"team_id": team_id, "active": {"$ne": False}},
                    {"password_hash": 0}
                )
            )
            
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error getting users by team: {e}")
            return []
    
    def search_users(
        self,
        query: str,
        include_inactive: bool = False
    ) -> List[Dict]:
        """
        Search users by name, email, or user_id
        
        Args:
            query: Search query
            include_inactive: Include inactive users
        
        Returns:
            list: List of matching user documents
        """
        try:
            search_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}},
                    {"user_id": {"$regex": query, "$options": "i"}}
                ]
            }
            
            if not include_inactive:
                search_query["active"] = {"$ne": False}
            
            users = list(self.collection.find(search_query, {"password_hash": 0}))
            
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error searching users: {e}")
            return []
    
    def get_user_count(
        self,
        include_inactive: bool = False,
        role: Optional[str] = None
    ) -> int:
        """
        Get total number of users
        
        Args:
            include_inactive: Include inactive users
            role: Filter by role
        
        Returns:
            int: User count
        """
        try:
            query = {}
            if not include_inactive:
                query["active"] = {"$ne": False}
            if role:
                query["role"] = role
            
            return self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"❌ Error counting users: {e}")
            return 0
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics
        
        Args:
            user_id: The user ID
        
        Returns:
            dict: User statistics
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {"error": "User not found"}
            
            # Get mood statistics
            mood_collection = db_manager.get_collection("mood_entries")
            
            from datetime import timedelta
            last_30d = datetime.utcnow() - timedelta(days=30)
            
            moods = list(mood_collection.find({
                "user_id": user_id,
                "timestamp": {"$gte": last_30d}
            }))
            
            # Calculate statistics
            from collections import Counter
            
            emotions = [m.get("dominant_emotion") for m in moods]
            stress_scores = [m.get("stress_score", 0) for m in moods]
            
            return {
                "user_id": user_id,
                "name": user.get("name"),
                "team_id": user.get("team_id"),
                "role": user.get("role"),
                "account_age_days": (datetime.utcnow() - user.get("created_at")).days,
                "last_login": user.get("last_login"),
                "login_count": user.get("_metadata", {}).get("login_count", 0),
                "mood_entries": len(moods),
                "avg_stress": round(sum(stress_scores) / len(stress_scores), 2) if stress_scores else 0,
                "emotion_distribution": dict(Counter(emotions)),
                "period": "last_30_days"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user statistics: {e}")
            return {"error": str(e)}
    
    def update_last_activity(self, user_id: str) -> bool:
        """
        Update user's last activity timestamp
        
        Args:
            user_id: The user ID
        
        Returns:
            bool: True if successful
        """
        try:
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Error updating last activity: {e}")
            return False
    
    def get_users_by_role(self, role: str) -> List[Dict]:
        """
        Get all users with a specific role
        
        Args:
            role: User role (employee, manager, hr, admin)
        
        Returns:
            list: Users with the specified role
        """
        try:
            users = list(
                self.collection.find(
                    {"role": role, "active": {"$ne": False}},
                    {"password_hash": 0}
                )
            )
            
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error getting users by role: {e}")
            return []
    
    def change_user_role(self, user_id: str, new_role: str) -> bool:
        """
        Change user's role
        
        Args:
            user_id: The user ID
            new_role: New role
        
        Returns:
            bool: True if successful
        """
        try:
            valid_roles = ["employee", "manager", "hr", "admin"]
            if new_role not in valid_roles:
                logger.error(f"❌ Invalid role: {new_role}")
                return False
            
            result = self.collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "role": new_role,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ User {user_id} role changed to {new_role}")
                self._clear_cache(f"user_{user_id}")
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error changing user role: {e}")
            return False
    
    def get_inactive_users(self, days: int = 30) -> List[Dict]:
        """
        Get users who haven't logged in for specified days
        
        Args:
            days: Number of days of inactivity
        
        Returns:
            list: Inactive users
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            users = list(
                self.collection.find(
                    {
                        "active": {"$ne": False},
                        "$or": [
                            {"last_login": {"$lt": cutoff_date}},
                            {"last_login": None}
                        ]
                    },
                    {"password_hash": 0}
                )
            )
            
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error getting inactive users: {e}")
            return []
    
    # Helper methods
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Set cache with timestamp"""
        self._cache[key] = (data, datetime.utcnow())
    
    def _clear_cache(self, key: str):
        """Clear specific cache entry"""
        if key in self._cache:
            del self._cache[key]
    
    def clear_all_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.debug("🗑️ User repository cache cleared")


# Create global repository instance
user_repo = UserRepository()