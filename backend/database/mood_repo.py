"""
Enhanced Mood Repository for Amdox
Production-grade mood/emotion tracking with advanced querying and analytics
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import BulkWriteError, DuplicateKeyError
import logging

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


class MoodRepository:
    """
    Enhanced repository for mood/emotion tracking database operations
    """
    
    def __init__(self):
        self.collection_name = "mood_entries"
        self._collection = None
        self._cache = {}
        self._cache_ttl = 60  # seconds
        logger.info("💭 Mood Repository initialized")
    
    @property
    def collection(self):
        """Get the mood_entries collection with lazy loading"""
        if self._collection is None:
            self._collection = db_manager.get_collection(self.collection_name)
        return self._collection
    
    def save_mood_entry(self, mood_data: Dict) -> Dict:
        """
        Save a new mood/emotion entry with validation
        
        Args:
            mood_data: Mood entry data dictionary
        
        Returns:
            dict: Saved mood entry with ID
        """
        try:
            # Validate required fields
            required_fields = ["user_id", "dominant_emotion", "stress_score"]
            for field in required_fields:
                if field not in mood_data:
                    logger.error(f"❌ Missing required field: {field}")
                    return {"error": f"Missing required field: {field}"}
            
            # Add timestamps
            mood_data["created_at"] = datetime.utcnow()
            if "timestamp" not in mood_data:
                mood_data["timestamp"] = datetime.utcnow()
            
            # Validate stress score range
            if not 0 <= mood_data["stress_score"] <= 10:
                return {"error": "stress_score must be between 0 and 10"}
            
            # Add metadata
            mood_data["_metadata"] = {
                "created_by": "system",
                "version": "1.0",
                "processed": True
            }
            
            result = self.collection.insert_one(mood_data)
            mood_data["_id"] = str(result.inserted_id)
            
            logger.debug(f"💾 Mood entry saved: {result.inserted_id}")
            
            # Clear cache for this user
            self._clear_user_cache(mood_data["user_id"])
            
            return mood_data
            
        except DuplicateKeyError as e:
            logger.error(f"❌ Duplicate mood entry: {e}")
            return {"error": "Duplicate mood entry"}
        except Exception as e:
            logger.error(f"❌ Error saving mood entry: {e}")
            return {"error": str(e)}
    
    def save_mood_entries_bulk(self, mood_entries: List[Dict]) -> Dict[str, Any]:
        """
        Save multiple mood entries in bulk
        
        Args:
            mood_entries: List of mood entry dictionaries
        
        Returns:
            dict: Bulk operation results
        """
        try:
            if not mood_entries:
                return {
                    "success": True,
                    "inserted_count": 0,
                    "message": "No entries to insert"
                }
            
            # Validate and prepare entries
            now = datetime.utcnow()
            for entry in mood_entries:
                if "created_at" not in entry:
                    entry["created_at"] = now
                if "timestamp" not in entry:
                    entry["timestamp"] = now
                
                entry["_metadata"] = {
                    "created_by": "system",
                    "version": "1.0",
                    "processed": True
                }
            
            # Insert in bulk
            result = self.collection.insert_many(mood_entries, ordered=False)
            
            logger.info(f"💾 Bulk saved {len(result.inserted_ids)} mood entries")
            
            return {
                "success": True,
                "inserted_count": len(result.inserted_ids),
                "inserted_ids": [str(id) for id in result.inserted_ids]
            }
            
        except BulkWriteError as e:
            logger.error(f"❌ Bulk write error: {e}")
            return {
                "success": False,
                "error": str(e),
                "inserted_count": e.details.get("nInserted", 0)
            }
        except Exception as e:
            logger.error(f"❌ Error in bulk save: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_mood_by_id(self, mood_id: str) -> Optional[Dict]:
        """
        Get mood entry by ID with caching
        
        Args:
            mood_id: The mood entry ID
        
        Returns:
            dict: Mood entry or None
        """
        try:
            # Check cache
            cache_key = f"mood_{mood_id}"
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            mood = self.collection.find_one({"_id": ObjectId(mood_id)})
            
            if mood:
                mood["_id"] = str(mood["_id"])
                self._set_cache(cache_key, mood)
            
            return mood
            
        except (InvalidId, Exception) as e:
            logger.error(f"❌ Error getting mood entry: {e}")
            return None
    
    def get_user_moods(
        self, 
        user_id: str, 
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "timestamp",
        sort_order: int = -1
    ) -> List[Dict]:
        """
        Get mood entries for a user with pagination
        
        Args:
            user_id: The user ID
            limit: Maximum number of entries to return
            skip: Number of entries to skip
            sort_by: Field to sort by
            sort_order: Sort order (1=ascending, -1=descending)
        
        Returns:
            list: List of mood entries
        """
        try:
            # Check cache
            cache_key = f"user_moods_{user_id}_{limit}_{skip}"
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            moods = list(
                self.collection
                .find({"user_id": user_id})
                .sort(sort_by, sort_order)
                .skip(skip)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for mood in moods:
                mood["_id"] = str(mood["_id"])
            
            self._set_cache(cache_key, moods)
            
            return moods
            
        except Exception as e:
            logger.error(f"❌ Error getting user moods: {e}")
            return []
    
    def get_user_moods_since(
        self, 
        user_id: str, 
        since: datetime,
        projection: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Get mood entries for a user since a specific time
        
        Args:
            user_id: The user ID
            since: Start datetime
            projection: Optional field projection
        
        Returns:
            list: List of mood entries
        """
        try:
            query = {
                "user_id": user_id,
                "timestamp": {"$gte": since}
            }
            
            cursor = self.collection.find(query, projection).sort("timestamp", -1)
            moods = list(cursor)
            
            for mood in moods:
                if "_id" in mood:
                    mood["_id"] = str(mood["_id"])
            
            return moods
            
        except Exception as e:
            logger.error(f"❌ Error getting user moods since: {e}")
            return []
    
    def get_user_moods_in_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Get mood entries for a user in a date range with filters
        
        Args:
            user_id: The user ID
            start_date: Start datetime
            end_date: End datetime
            filters: Additional filter criteria
        
        Returns:
            list: List of mood entries
        """
        try:
            query = {
                "user_id": user_id,
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            # Add additional filters
            if filters:
                query.update(filters)
            
            moods = list(
                self.collection
                .find(query)
                .sort("timestamp", -1)
            )
            
            for mood in moods:
                mood["_id"] = str(mood["_id"])
            
            return moods
            
        except Exception as e:
            logger.error(f"❌ Error getting user moods in range: {e}")
            return []
    
    def get_session_moods(
        self, 
        session_id: str,
        include_statistics: bool = False
    ) -> Dict[str, Any]:
        """
        Get all mood entries for a session with optional statistics
        
        Args:
            session_id: The session ID
            include_statistics: Include statistical analysis
        
        Returns:
            dict: Session moods with optional statistics
        """
        try:
            moods = list(
                self.collection
                .find({"session_id": session_id})
                .sort("timestamp", -1)
            )
            
            for mood in moods:
                mood["_id"] = str(mood["_id"])
            
            result = {
                "session_id": session_id,
                "count": len(moods),
                "moods": moods
            }
            
            if include_statistics and moods:
                result["statistics"] = self._calculate_session_statistics(moods)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting session moods: {e}")
            return {"session_id": session_id, "count": 0, "moods": []}
    
    def get_dominant_emotions(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, int]:
        """
        Get dominant emotions for a user over a period with counts
        
        Args:
            user_id: The user ID
            days: Number of days to look back
        
        Returns:
            dict: Emotion counts sorted by frequency
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
            logger.error(f"❌ Error getting dominant emotions: {e}")
            return {}
    
    def get_average_stress(
        self, 
        user_id: str, 
        days: int = 30,
        include_breakdown: bool = False
    ) -> Dict[str, Any]:
        """
        Get average stress score for a user with optional breakdown
        
        Args:
            user_id: The user ID
            days: Number of days to look back
            include_breakdown: Include daily/weekly breakdown
        
        Returns:
            dict: Average stress score with optional breakdown
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
                {
                    "$group": {
                        "_id": None,
                        "avg_stress": {"$avg": "$stress_score"},
                        "max_stress": {"$max": "$stress_score"},
                        "min_stress": {"$min": "$stress_score"},
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if not result:
                return {"average": 0.0, "max": 0, "min": 0, "count": 0}
            
            stats = result[0]
            response = {
                "average": round(stats.get("avg_stress", 0), 2),
                "max": stats.get("max_stress", 0),
                "min": stats.get("min_stress", 0),
                "count": stats.get("count", 0)
            }
            
            if include_breakdown:
                response["breakdown"] = self._get_stress_breakdown(user_id, since)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error getting average stress: {e}")
            return {"average": 0.0, "max": 0, "min": 0, "count": 0}
    
    def get_emotion_trends(
        self, 
        user_id: str,
        days: int = 30,
        granularity: str = "daily"
    ) -> List[Dict]:
        """
        Get emotion trends over time with different granularities
        
        Args:
            user_id: The user ID
            days: Number of days to analyze
            granularity: Time granularity (hourly/daily/weekly)
        
        Returns:
            list: Trend data points
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Determine date format based on granularity
            format_map = {
                "hourly": "%Y-%m-%d %H:00",
                "daily": "%Y-%m-%d",
                "weekly": "%Y-W%U"
            }
            date_format = format_map.get(granularity, "%Y-%m-%d")
            
            pipeline = [
                {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
                {
                    "$group": {
                        "_id": {
                            "period": {
                                "$dateToString": {
                                    "format": date_format,
                                    "date": "$timestamp"
                                }
                            },
                            "emotion": "$dominant_emotion"
                        },
                        "count": {"$sum": 1},
                        "avg_stress": {"$avg": "$stress_score"}
                    }
                },
                {"$sort": {"_id.period": 1}}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Format results
            trends = []
            for r in results:
                trends.append({
                    "period": r["_id"]["period"],
                    "emotion": r["_id"]["emotion"],
                    "count": r["count"],
                    "avg_stress": round(r["avg_stress"], 2)
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"❌ Error getting emotion trends: {e}")
            return []
    
    def update_mood_entry(
        self, 
        mood_id: str, 
        update_data: Dict
    ) -> bool:
        """
        Update a mood entry with validation
        
        Args:
            mood_id: The mood entry ID
            update_data: Fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate stress score if present
            if "stress_score" in update_data:
                if not 0 <= update_data["stress_score"] <= 10:
                    logger.error("❌ Invalid stress_score")
                    return False
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(mood_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.debug(f"✅ Updated mood entry: {mood_id}")
                
                # Clear cache
                mood = self.collection.find_one({"_id": ObjectId(mood_id)})
                if mood and "user_id" in mood:
                    self._clear_user_cache(mood["user_id"])
            
            return result.modified_count > 0
            
        except (InvalidId, Exception) as e:
            logger.error(f"❌ Error updating mood entry: {e}")
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
            # Get user_id before deleting for cache clear
            mood = self.collection.find_one({"_id": ObjectId(mood_id)})
            
            result = self.collection.delete_one({"_id": ObjectId(mood_id)})
            
            if result.deleted_count > 0:
                logger.debug(f"🗑️ Deleted mood entry: {mood_id}")
                
                if mood and "user_id" in mood:
                    self._clear_user_cache(mood["user_id"])
            
            return result.deleted_count > 0
            
        except (InvalidId, Exception) as e:
            logger.error(f"❌ Error deleting mood entry: {e}")
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
            
            if result.deleted_count > 0:
                logger.info(f"🗑️ Deleted {result.deleted_count} mood entries for user {user_id}")
                self._clear_user_cache(user_id)
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error deleting user moods: {e}")
            return 0
    
    def delete_old_moods(self, days: int = 90) -> int:
        """
        Delete mood entries older than specified days
        
        Args:
            days: Delete entries older than this many days
        
        Returns:
            int: Number of deleted entries
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            logger.info(f"🗑️ Deleted {result.deleted_count} old mood entries")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error deleting old moods: {e}")
            return 0
    
    def get_mood_count(
        self, 
        user_id: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> int:
        """
        Get mood entry count with optional filters
        
        Args:
            user_id: Optional user ID to filter by
            filters: Additional filter criteria
        
        Returns:
            int: Count of mood entries
        """
        try:
            query = {}
            if user_id:
                query["user_id"] = user_id
            if filters:
                query.update(filters)
            
            return self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"❌ Error counting mood entries: {e}")
            return 0
    
    def search_moods(
        self,
        query: Dict,
        limit: int = 100,
        projection: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Advanced mood search with custom query
        
        Args:
            query: MongoDB query dictionary
            limit: Maximum results
            projection: Field projection
        
        Returns:
            list: Matching mood entries
        """
        try:
            cursor = self.collection.find(query, projection).limit(limit)
            moods = list(cursor)
            
            for mood in moods:
                if "_id" in mood:
                    mood["_id"] = str(mood["_id"])
            
            return moods
            
        except Exception as e:
            logger.error(f"❌ Error searching moods: {e}")
            return []
    
    def get_high_stress_users(
        self,
        threshold: int = 7,
        days: int = 7
    ) -> List[Dict]:
        """
        Get users with consistently high stress levels
        
        Args:
            threshold: Stress score threshold
            days: Number of days to analyze
        
        Returns:
            list: Users with high stress
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": since}, "stress_score": {"$gte": threshold}}},
                {
                    "$group": {
                        "_id": "$user_id",
                        "high_stress_count": {"$sum": 1},
                        "avg_stress": {"$avg": "$stress_score"},
                        "max_stress": {"$max": "$stress_score"}
                    }
                },
                {"$match": {"high_stress_count": {"$gte": 3}}},  # At least 3 high-stress events
                {"$sort": {"avg_stress": -1}}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            return [
                {
                    "user_id": r["_id"],
                    "high_stress_count": r["high_stress_count"],
                    "avg_stress": round(r["avg_stress"], 2),
                    "max_stress": r["max_stress"]
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting high stress users: {e}")
            return []
    
    # Helper methods
    
    def _calculate_session_statistics(self, moods: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for a session"""
        try:
            from collections import Counter
            
            emotions = [m.get("dominant_emotion") for m in moods]
            stress_scores = [m.get("stress_score", 0) for m in moods]
            confidences = [m.get("confidence", 0) for m in moods]
            
            emotion_counter = Counter(emotions)
            
            return {
                "total_entries": len(moods),
                "dominant_emotion": emotion_counter.most_common(1)[0][0],
                "emotion_distribution": dict(emotion_counter),
                "avg_stress": round(sum(stress_scores) / len(stress_scores), 2),
                "max_stress": max(stress_scores),
                "min_stress": min(stress_scores),
                "avg_confidence": round(sum(confidences) / len(confidences), 3)
            }
        except Exception:
            return {}
    
    def _get_stress_breakdown(self, user_id: str, since: datetime) -> Dict[str, Any]:
        """Get stress breakdown by day"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                        },
                        "avg_stress": {"$avg": "$stress_score"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            return {
                r["_id"]: {
                    "avg_stress": round(r["avg_stress"], 2),
                    "count": r["count"]
                }
                for r in results
            }
        except Exception:
            return {}
    
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
    
    def _clear_user_cache(self, user_id: str):
        """Clear all cache entries for a user"""
        keys_to_remove = [k for k in self._cache.keys() if user_id in k]
        for key in keys_to_remove:
            del self._cache[key]
    
    def clear_all_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.info("🗑️ Mood repository cache cleared")


# Create global repository instance
mood_repo = MoodRepository()