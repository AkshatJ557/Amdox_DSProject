"""
User repository for database operations
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager


class UserRepository:
    """
    Repository for user-related database operations
    """
    
    def __init__(self):
        self.collection_name = "users"
        self._collection = None
    
    @property
    def collection(self):
        """Get the users collection"""
        if self._collection is None:
            self._collection = db_manager.get_collection(self.collection_name)
        return self._collection
    
    def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user
        
        Args:
            user_data: User information dictionary
        
        Returns:
            dict: Created user document
        """
        try:
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.insert_one(user_data)
            user_data["_id"] = str(result.inserted_id)
            return user_data
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return {"error": str(e)}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user by user_id
        
        Args:
            user_id: The user ID
        
        Returns:
            dict: User document or None
        """
        try:
            return self.collection.find_one({"user_id": user_id})
        except Exception as e:
            print(f"❌ Error getting user: {e}")
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
            return self.collection.find_one({"email": email})
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
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
            update_data["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user
        
        Args:
            user_id: The user ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all users
        
        Returns:
            list: List of user documents
        """
        try:
            return list(self.collection.find({}))
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
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
            return list(self.collection.find({"team_id": team_id}))
        except Exception as e:
            print(f"❌ Error getting users by team: {e}")
            return []
    
    def search_users(self, query: str) -> List[Dict]:
        """
        Search users by name or email
        
        Args:
            query: Search query
        
        Returns:
            list: List of matching user documents
        """
        try:
            return list(self.collection.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}}
                ]
            }))
        except Exception as e:
            print(f"❌ Error searching users: {e}")
            return []
    
    def get_user_count(self) -> int:
        """
        Get total number of users
        
        Returns:
            int: User count
        """
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"❌ Error counting users: {e}")
            return 0


# Create global repository instance
user_repo = UserRepository()

