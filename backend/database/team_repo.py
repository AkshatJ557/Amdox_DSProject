"""
Team repository for team-related database operations
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager


class TeamRepository:
    """
    Repository for team-related database operations
    """
    
    def __init__(self):
        self.collection_name = "teams"
        self._collection = None
    
    @property
    def collection(self):
        """Get the teams collection"""
        if self._collection is None:
            self._collection = db_manager.get_collection(self.collection_name)
        return self._collection
    
    def create_team(self, team_data: Dict) -> Dict:
        """
        Create a new team
        
        Args:
            team_data: Team information dictionary
        
        Returns:
            dict: Created team document
        """
        try:
            team_data["created_at"] = datetime.utcnow()
            team_data["updated_at"] = datetime.utcnow()
            team_data["member_count"] = len(team_data.get("members", []))
            
            result = self.collection.insert_one(team_data)
            team_data["_id"] = str(result.inserted_id)
            return team_data
        except Exception as e:
            print(f"❌ Error creating team: {e}")
            return {"error": str(e)}
    
    def get_team_by_id(self, team_id: str) -> Optional[Dict]:
        """
        Get team by team_id
        
        Args:
            team_id: The team ID
        
        Returns:
            dict: Team document or None
        """
        try:
            return self.collection.find_one({"team_id": team_id})
        except Exception as e:
            print(f"❌ Error getting team: {e}")
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
            return self.collection.find_one({"name": name})
        except Exception as e:
            print(f"❌ Error getting team by name: {e}")
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
            if "members" in update_data:
                update_data["member_count"] = len(update_data["members"])
            
            result = self.collection.update_one(
                {"team_id": team_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating team: {e}")
            return False
    
    def delete_team(self, team_id: str) -> bool:
        """
        Delete a team
        
        Args:
            team_id: The team ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"team_id": team_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Error deleting team: {e}")
            return False
    
    def get_all_teams(self) -> List[Dict]:
        """
        Get all teams
        
        Returns:
            list: List of team documents
        """
        try:
            return list(self.collection.find({}))
        except Exception as e:
            print(f"❌ Error getting all teams: {e}")
            return []
    
    def add_member(self, team_id: str, user_id: str) -> bool:
        """
        Add a member to a team
        
        Args:
            team_id: The team ID
            user_id: User ID to add
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"team_id": team_id},
                {
                    "$addToSet": {"members": user_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error adding team member: {e}")
            return False
    
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
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error removing team member: {e}")
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
            team = self.collection.find_one({"team_id": team_id})
            return team.get("members", []) if team else []
        except Exception as e:
            print(f"❌ Error getting team members: {e}")
            return []
    
    def get_team_count(self) -> int:
        """
        Get total number of teams
        
        Returns:
            int: Team count
        """
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"❌ Error counting teams: {e}")
            return 0
    
    def search_teams(self, query: str) -> List[Dict]:
        """
        Search teams by name or description
        
        Args:
            query: Search query
        
        Returns:
            list: List of matching team documents
        """
        try:
            return list(self.collection.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}}
                ]
            }))
        except Exception as e:
            print(f"❌ Error searching teams: {e}")
            return []


# Create global repository instance
team_repo = TeamRepository()

