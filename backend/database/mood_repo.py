"""
Mood repository for emotion/mood tracking database operations
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId
from bson.errors import InvalidId

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager


class MoodRepository:
    """
    Repository for mood/emotion tracking database operations
    """
    
    def __init__(self):
        self.collection_name = "mood_entries"
        self._collection = None
    
    @property
    def collection(self):
        """Get the mood_entries collection"""
        if self._collection is None:
            self._collection = db_manager.get_collection(self.collection_name)
        return self._collection
    
    def save_mood_entry(self, mood_data: Dict) -> Dict:
        """
        Save a new mood/emotion entry
        
        Args:
            mood_data: Mood entry data dictionary
        
        Returns:
            dict: Saved mood entry with ID
        """
        try:
            mood_data["created_at"] = datetime.utcnow()
            if "timestamp" not in mood_data:
                mood_data["timestamp"] = datetime.utcnow()
            
            result = self.collection.insert_one(mood_data)
            mood_data["_id"] = str(result.inserted_id)
            return mood_data
        except Exception as e:
            print(f"❌ Error saving mood entry: {e}")
            return {"error": str(e)}
    
    def get_mood_by_id(self, mood_id: str) -> Optional[Dict]:
        """
        Get mood entry by ID
        
        Args:
            mood_id: The mood entry ID
        
        Returns:
            dict: Mood entry or None
        """
        try:
            return self.collection.find_one({"_id": ObjectId(mood_id)})
        except (InvalidId, Exception) as e:
            print(f"❌ Error getting mood entry: {e}")
            return None
    
    def get_user_moods(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get mood entries for a user
        
        Args:
            user_id: The user ID
            limit: Maximum number of entries to return
        
        Returns:
            list: List of mood entries
        """
        try:
            return list(
                self.collection
                .find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
        except Exception as e:
            print(f"❌ Error getting user moods: {e}")
            return []
    
    def get_user_moods_since(self, user_id: str, since: datetime) -> List[Dict]:
        """
        Get mood entries for a user since a specific time
        
        Args:
            user_id: The user ID
            since: Start datetime
        
        Returns:
            list: List of mood entries
        """
        try:
            return list(
                self.collection
                .find({
                    "user_id": user_id,
                    "timestamp": {"$gte": since}
                })
                .sort("timestamp", -1)
            )
        except Exception as e:
            print(f"❌ Error getting user moods since: {e}")
            return []
    
    def get_user_moods_in_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict]:
        """
        Get mood entries for a user in a date range
        
        Args:
            user_id: The user ID
            start_date: Start datetime
            end_date: End datetime
        
        Returns:
            list: List of mood entries
        """
        try:
            return list(
                self.collection
                .find({
                    "user_id": user_id,
                    "timestamp": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                })
                .sort("timestamp", -1)
            )
        except Exception as e:
            print(f"❌ Error getting user moods in range: {e}")
            return []
    
    def get_session_moods(self, session_id: str) -> List[Dict]:
        """
        Get all mood entries for a session
        
        Args:
            session_id: The session ID
        
        Returns:
            list: List of mood entries
        """
        try:
            return list(
                self.collection
                .find({"session_id": session_id})
                .sort("timestamp", -1)
            )
        except Exception as e:
            print(f"❌ Error getting session moods: {e}")
            return []
    
    def get_dominant_emotions(self, user_id: str, days: int = 30) -> Dict[str, int]:
        """
        Get dominant emotions for a user over a period
        
        Args:
            user_id: The user ID
            days: Number of days to look back
        
        Returns:
            dict: Emotion counts
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
                {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return {r["_id"]: r["count"] for r in results}
        except Exception as e:
            print(f"❌ Error getting dominant emotions: {e}")
            return {}
    
    def get_average_stress(self, user_id: str, days: int = 30) -> float:
        """
        Get average stress score for a user over a period
        
        Args:
            user_id: The user ID
            days: Number of days to look back
        
        Returns:
            float: Average stress score
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
                {"$group": {"_id": None, "avg_stress": {"$avg": "$stress_score"}}}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            return result[0]["avg_stress"] if result else 0.0
        except Exception as e:
            print(f"❌ Error getting average stress: {e}")
            return 0.0
    
    def update_mood_entry(self, mood_id: str, update_data: Dict) -> bool:
        """
        Update a mood entry
        
        Args:
            mood_id: The mood entry ID
            update_data: Fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(mood_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except (InvalidId, Exception) as e:
            print(f"❌ Error updating mood entry: {e}")
            return False
    
    def delete_mood_entry(self, mood_id: str) -> bool:
        """
        Delete a mood entry
        
        Args:
            mood_id: The mood entry ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(mood_id)})
            return result.deleted_count > 0
        except (InvalidId, Exception) as e:
            print(f"❌ Error deleting mood entry: {e}")
            return False
    
    def delete_user_moods(self, user_id: str) -> int:
        """
        Delete all mood entries for a user
        
        Args:
            user_id: The user ID
        
        Returns:
            int: Number of deleted entries
        """
        try:
            result = self.collection.delete_many({"user_id": user_id})
            return result.deleted_count
        except Exception as e:
            print(f"❌ Error deleting user moods: {e}")
            return 0
    
    def get_mood_count(self, user_id: str = None) -> int:
        """
        Get mood entry count
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            int: Count of mood entries
        """
        try:
            query = {} if user_id is None else {"user_id": user_id}
            return self.collection.count_documents(query)
        except Exception as e:
            print(f"❌ Error counting mood entries: {e}")
            return 0


# Create global repository instance
mood_repo = MoodRepository()

