"""
Enhanced Team Repository for Amdox
Production-grade team management with member tracking and analytics
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
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


class TeamRepository:
    """
    Enhanced repository for team-related database operations
    """
    
    def __init__(self):
        self.collection_name = "teams"
        self._collection = None
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes for teams
        logger.info("👥 Team Repository initialized")
    
    @property
    def collection(self):
        """Get the teams collection with lazy loading"""
        if self._collection is None:
            self._collection = db_manager.get_collection(self.collection_name)
        return self._collection
    
    def create_team(self, team_data: Dict) -> Dict:
        """
        Create a new team with validation
        
        Args:
            team_data: Team information dictionary
        
        Returns:
            dict: Created team document
        """
        try:
            # Validate required fields
            required_fields = ["team_id", "name"]
            for field in required_fields:
                if field not in team_data:
                    logger.error(f"❌ Missing required field: {field}")
                    return {"error": f"Missing required field: {field}"}
            
            # Add timestamps and metadata
            team_data["created_at"] = datetime.utcnow()
            team_data["updated_at"] = datetime.utcnow()
            team_data["member_count"] = len(team_data.get("members", []))
            team_data["active"] = team_data.get("active", True)
            
            # Add metadata
            team_data["_metadata"] = {
                "created_by": team_data.get("manager_id", "system"),
                "version": "1.0"
            }
            
            # Ensure members is a list
            if "members" not in team_data:
                team_data["members"] = []
            
            result = self.collection.insert_one(team_data)
            team_data["_id"] = str(result.inserted_id)
            
            logger.info(f"✅ Team created: {team_data['team_id']} ({team_data['name']})")
            
            # Clear cache
            self.clear_all_cache()
            
            return team_data
            
        except DuplicateKeyError as e:
            logger.error(f"❌ Duplicate team_id: {e}")
            return {"error": "Team ID already exists"}
        except Exception as e:
            logger.error(f"❌ Error creating team: {e}")
            return {"error": str(e)}
    
    def get_team_by_id(self, team_id: str) -> Optional[Dict]:
        """
        Get team by team_id with caching
        
        Args:
            team_id: The team ID
        
        Returns:
            dict: Team document or None
        """
        try:
            # Check cache
            cache_key = f"team_{team_id}"
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            team = self.collection.find_one({"team_id": team_id})
            
            if team:
                team["_id"] = str(team["_id"])
                self._set_cache(cache_key, team)
            
            return team
            
        except Exception as e:
            logger.error(f"❌ Error getting team: {e}")
            return None
    
    def get_team_by_name(self, name: str) -> Optional[Dict]:
        """
        Get team by name
        
        Args:
            name: Team name
        
        Returns:
            dict: Team document or None
        """
        try:
            team = self.collection.find_one({"name": name})
            
            if team:
                team["_id"] = str(team["_id"])
            
            return team
            
        except Exception as e:
            logger.error(f"❌ Error getting team by name: {e}")
            return None
    
    def get_team_with_members(self, team_id: str) -> Optional[Dict]:
        """
        Get team with populated member information
        
        Args:
            team_id: The team ID
        
        Returns:
            dict: Team with member details
        """
        try:
            team = self.get_team_by_id(team_id)
            
            if not team:
                return None
            
            # Get member details
            if team.get("members"):
                user_collection = db_manager.get_collection("users")
                members = list(user_collection.find({
                    "user_id": {"$in": team["members"]}
                }))
                
                # Convert ObjectIds and add to team
                for member in members:
                    member["_id"] = str(member["_id"])
                
                team["member_details"] = members
            else:
                team["member_details"] = []
            
            return team
            
        except Exception as e:
            logger.error(f"❌ Error getting team with members: {e}")
            return None
    
    def update_team(self, team_id: str, update_data: Dict) -> bool:
        """
        Update team information
        
        Args:
            team_id: The team ID
            update_data: Fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update member count if members list changed
            if "members" in update_data:
                update_data["member_count"] = len(update_data["members"])
            
            result = self.collection.update_one(
                {"team_id": team_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Team updated: {team_id}")
                self._clear_cache(f"team_{team_id}")
                self.clear_all_cache()
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating team: {e}")
            return False
    
    def delete_team(self, team_id: str) -> bool:
        """
        Delete a team (soft delete by marking inactive)
        
        Args:
            team_id: The team ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Soft delete - mark as inactive
            result = self.collection.update_one(
                {"team_id": team_id},
                {
                    "$set": {
                        "active": False,
                        "deleted_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🗑️ Team soft-deleted: {team_id}")
                self._clear_cache(f"team_{team_id}")
                self.clear_all_cache()
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error deleting team: {e}")
            return False
    
    def hard_delete_team(self, team_id: str) -> bool:
        """
        Permanently delete a team
        
        Args:
            team_id: The team ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"team_id": team_id})
            
            if result.deleted_count > 0:
                logger.warning(f"⚠️ Team permanently deleted: {team_id}")
                self._clear_cache(f"team_{team_id}")
                self.clear_all_cache()
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error hard deleting team: {e}")
            return False
    
    def get_all_teams(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all teams with pagination
        
        Args:
            include_inactive: Include inactive teams
            skip: Number to skip
            limit: Maximum to return
        
        Returns:
            list: List of team documents
        """
        try:
            query = {}
            if not include_inactive:
                query["active"] = {"$ne": False}
            
            teams = list(
                self.collection
                .find(query)
                .skip(skip)
                .limit(limit)
                .sort("created_at", -1)
            )
            
            for team in teams:
                team["_id"] = str(team["_id"])
            
            return teams
            
        except Exception as e:
            logger.error(f"❌ Error getting all teams: {e}")
            return []
    
    def add_member(self, team_id: str, user_id: str) -> bool:
        """
        Add a member to a team with validation
        
        Args:
            team_id: The team ID
            user_id: User ID to add
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if user is already a member
            team = self.get_team_by_id(team_id)
            if team and user_id in team.get("members", []):
                logger.warning(f"⚠️ User {user_id} already in team {team_id}")
                return True
            
            result = self.collection.update_one(
                {"team_id": team_id},
                {
                    "$addToSet": {"members": user_id},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {"member_count": 1}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Added member {user_id} to team {team_id}")
                self._clear_cache(f"team_{team_id}")
                
                # Update user's team_id
                user_collection = db_manager.get_collection("users")
                user_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"team_id": team_id, "updated_at": datetime.utcnow()}}
                )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error adding team member: {e}")
            return False
    
    def add_members_bulk(self, team_id: str, user_ids: List[str]) -> Dict[str, Any]:
        """
        Add multiple members to a team at once
        
        Args:
            team_id: The team ID
            user_ids: List of user IDs to add
        
        Returns:
            dict: Results with added count
        """
        try:
            if not user_ids:
                return {"success": True, "added_count": 0}
            
            # Get current members
            team = self.get_team_by_id(team_id)
            if not team:
                return {"success": False, "error": "Team not found"}
            
            current_members = set(team.get("members", []))
            new_members = [uid for uid in user_ids if uid not in current_members]
            
            if not new_members:
                return {"success": True, "added_count": 0, "message": "All users already members"}
            
            result = self.collection.update_one(
                {"team_id": team_id},
                {
                    "$addToSet": {"members": {"$each": new_members}},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {"member_count": len(new_members)}
                }
            )
            
            # Update users' team_id
            user_collection = db_manager.get_collection("users")
            user_collection.update_many(
                {"user_id": {"$in": new_members}},
                {"$set": {"team_id": team_id, "updated_at": datetime.utcnow()}}
            )
            
            logger.info(f"✅ Added {len(new_members)} members to team {team_id}")
            self._clear_cache(f"team_{team_id}")
            
            return {
                "success": True,
                "added_count": len(new_members),
                "skipped_count": len(user_ids) - len(new_members)
            }
            
        except Exception as e:
            logger.error(f"❌ Error adding members in bulk: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_member(self, team_id: str, user_id: str) -> bool:
        """
        Remove a member from a team
        
        Args:
            team_id: The team ID
            user_id: User ID to remove
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"team_id": team_id},
                {
                    "$pull": {"members": user_id},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {"member_count": -1}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Removed member {user_id} from team {team_id}")
                self._clear_cache(f"team_{team_id}")
                
                # Clear user's team_id
                user_collection = db_manager.get_collection("users")
                user_collection.update_one(
                    {"user_id": user_id},
                    {"$unset": {"team_id": ""}, "$set": {"updated_at": datetime.utcnow()}}
                )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error removing team member: {e}")
            return False
    
    def get_team_members(self, team_id: str) -> List[str]:
        """
        Get all member IDs for a team
        
        Args:
            team_id: The team ID
        
        Returns:
            list: List of user IDs
        """
        try:
            team = self.get_team_by_id(team_id)
            return team.get("members", []) if team else []
            
        except Exception as e:
            logger.error(f"❌ Error getting team members: {e}")
            return []
    
    def get_team_size(self, team_id: str) -> int:
        """
        Get team member count
        
        Args:
            team_id: The team ID
        
        Returns:
            int: Number of members
        """
        try:
            team = self.get_team_by_id(team_id)
            return team.get("member_count", 0) if team else 0
            
        except Exception as e:
            logger.error(f"❌ Error getting team size: {e}")
            return 0
    
    def get_team_count(self, include_inactive: bool = False) -> int:
        """
        Get total number of teams
        
        Args:
            include_inactive: Include inactive teams
        
        Returns:
            int: Team count
        """
        try:
            query = {}
            if not include_inactive:
                query["active"] = {"$ne": False}
            
            return self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"❌ Error counting teams: {e}")
            return 0
    
    def search_teams(
        self,
        query: str,
        include_inactive: bool = False
    ) -> List[Dict]:
        """
        Search teams by name or description
        
        Args:
            query: Search query
            include_inactive: Include inactive teams
        
        Returns:
            list: List of matching team documents
        """
        try:
            search_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"team_id": {"$regex": query, "$options": "i"}}
                ]
            }
            
            if not include_inactive:
                search_query["active"] = {"$ne": False}
            
            teams = list(self.collection.find(search_query))
            
            for team in teams:
                team["_id"] = str(team["_id"])
            
            return teams
            
        except Exception as e:
            logger.error(f"❌ Error searching teams: {e}")
            return []
    
    def get_team_statistics(self, team_id: str) -> Dict[str, Any]:
        """
        Get comprehensive team statistics
        
        Args:
            team_id: The team ID
        
        Returns:
            dict: Team statistics
        """
        try:
            team = self.get_team_by_id(team_id)
            if not team:
                return {"error": "Team not found"}
            
            # Get mood statistics
            mood_collection = db_manager.get_collection("mood_entries")
            
            from datetime import timedelta
            last_30d = datetime.utcnow() - timedelta(days=30)
            
            # Get all moods for team members
            member_ids = team.get("members", [])
            
            if not member_ids:
                return {
                    "team_id": team_id,
                    "member_count": 0,
                    "mood_entries": 0,
                    "avg_stress": 0,
                    "emotion_distribution": {}
                }
            
            moods = list(mood_collection.find({
                "user_id": {"$in": member_ids},
                "timestamp": {"$gte": last_30d}
            }))
            
            # Calculate statistics
            from collections import Counter
            
            emotions = [m.get("dominant_emotion") for m in moods]
            stress_scores = [m.get("stress_score", 0) for m in moods]
            
            return {
                "team_id": team_id,
                "team_name": team.get("name"),
                "member_count": len(member_ids),
                "mood_entries": len(moods),
                "avg_stress": round(sum(stress_scores) / len(stress_scores), 2) if stress_scores else 0,
                "max_stress": max(stress_scores) if stress_scores else 0,
                "min_stress": min(stress_scores) if stress_scores else 0,
                "emotion_distribution": dict(Counter(emotions)),
                "period": "last_30_days"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting team statistics: {e}")
            return {"error": str(e)}
    
    def get_teams_by_manager(self, manager_id: str) -> List[Dict]:
        """
        Get all teams managed by a specific manager
        
        Args:
            manager_id: Manager user ID
        
        Returns:
            list: Teams managed by this user
        """
        try:
            teams = list(self.collection.find({
                "manager_id": manager_id,
                "active": {"$ne": False}
            }))
            
            for team in teams:
                team["_id"] = str(team["_id"])
            
            return teams
            
        except Exception as e:
            logger.error(f"❌ Error getting teams by manager: {e}")
            return []
    
    def update_team_manager(self, team_id: str, new_manager_id: str) -> bool:
        """
        Update team manager
        
        Args:
            team_id: The team ID
            new_manager_id: New manager user ID
        
        Returns:
            bool: True if successful
        """
        try:
            result = self.collection.update_one(
                {"team_id": team_id},
                {
                    "$set": {
                        "manager_id": new_manager_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Team {team_id} manager updated to {new_manager_id}")
                self._clear_cache(f"team_{team_id}")
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating team manager: {e}")
            return False
    
    # Helper methods
    
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
        logger.debug("🗑️ Team repository cache cleared")


# Create global repository instance
team_repo = TeamRepository()