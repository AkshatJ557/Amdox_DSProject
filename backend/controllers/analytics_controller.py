"""
Analytics controller for generating reports and insights
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager
from backend.services.aggregation_service import aggregation_service


class AnalyticsController:
    """
    Controller for analytics and reporting endpoints
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
    
    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """
        Get dashboard analytics summary
        
        Returns:
            dict: Dashboard analytics
        """
        try:
            # Get basic counts
            users_count = self.db.users.count_documents({})
            teams_count = self.db.teams.count_documents({})
            mood_entries_count = self.db.mood_entries.count_documents({})
            
            # Get recent activity (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_entries = self.db.mood_entries.count_documents({
                "timestamp": {"$gte": last_24h}
            })
            
            # Get emotion distribution (last 7 days)
            last_7d = datetime.utcnow() - timedelta(days=7)
            emotion_pipeline = [
                {"$match": {"timestamp": {"$gte": last_7d}}},
                {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            emotion_results = list(self.db.mood_entries.aggregate(emotion_pipeline))
            
            emotion_distribution = {
                r["_id"]: r["count"] for r in emotion_results
            }
            
            # Calculate average stress
            stress_pipeline = [
                {"$match": {"timestamp": {"$gte": last_7d}}},
                {"$group": {"_id": None, "avg_stress": {"$avg": "$stress_score"}}}
            ]
            stress_result = list(self.db.mood_entries.aggregate(stress_pipeline))
            avg_stress = stress_result[0]["avg_stress"] if stress_result else 0
            
            return {
                "success": True,
                "dashboard": {
                    "total_users": users_count,
                    "total_teams": teams_count,
                    "total_mood_entries": mood_entries_count,
                    "recent_24h_entries": recent_entries,
                    "emotion_distribution_last_7d": emotion_distribution,
                    "average_stress_last_7d": round(avg_stress, 2),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting dashboard analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_emotion_analytics_report(
        self, 
        days: int = 30, 
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get emotion analytics report
        
        Args:
            days: Number of days to analyze
            team_id: Optional team ID to filter by
        
        Returns:
            dict: Emotion analytics report
        """
        try:
            result = aggregation_service.aggregate_emotion_distribution(team_id, days)
            return result
            
        except Exception as e:
            print(f"❌ Error getting emotion analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stress_analytics_report(
        self, 
        days: int = 30, 
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get stress analytics report
        
        Args:
            days: Number of days to analyze
            team_id: Optional team ID to filter by
        
        Returns:
            dict: Stress analytics report
        """
        try:
            result = aggregation_service.aggregate_team_stress(team_id, days)
            return result
            
        except Exception as e:
            print(f"❌ Error getting stress analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_activity_report(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user activity report
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            dict: User activity report
        """
        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get mood entries
            entries = list(
                self.db.mood_entries
                .find({"user_id": user_id, "timestamp": {"$gte": start_date}})
                .sort("timestamp", -1)
            )
            
            if not entries:
                return {
                    "success": True,
                    "message": "No activity data available",
                    "user_id": user_id,
                    "report": {
                        "total_entries": 0,
                        "emotion_distribution": {},
                        "avg_stress": 0,
                        "activity_by_day": {}
                    }
                }
            
            # Calculate emotion distribution
            from collections import Counter, defaultdict
            emotion_counter = Counter(e.get("dominant_emotion", "Unknown") for e in entries)
            
            # Calculate stress over time
            stress_scores = [e.get("stress_score", 0) for e in entries]
            avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
            
            # Activity by day
            activity_by_day = defaultdict(int)
            for entry in entries:
                day = entry.get("timestamp", datetime.utcnow()).strftime("%Y-%m-%d")
                activity_by_day[day] += 1
            
            # Get stress patterns
            stress_patterns = aggregation_service.analyze_stress_patterns(user_id, days)
            
            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "report": {
                    "total_entries": len(entries),
                    "emotion_distribution": dict(emotion_counter),
                    "avg_stress": round(avg_stress, 2),
                    "activity_by_day": dict(sorted(activity_by_day.items())),
                    "stress_analysis": stress_patterns.get("analysis", {})
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting user activity report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_team_report(
        self, 
        team_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive team report
        
        Args:
            team_id: Team ID
            days: Number of days to analyze
        
        Returns:
            dict: Team report
        """
        try:
            result = aggregation_service.generate_team_report(team_id, days)
            return result
            
        except Exception as e:
            print(f"❌ Error getting team report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trending_emotions(
        self, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get trending emotions over time
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: Trending emotions
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": {
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                            "emotion": "$dominant_emotion"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.date": 1, "count": -1}}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            # Organize by date
            from collections import defaultdict
            by_date = defaultdict(list)
            for r in results:
                date = r["_id"]["date"]
                emotion = r["_id"]["emotion"]
                by_date[date].append({
                    "emotion": emotion,
                    "count": r["count"]
                })
            
            return {
                "success": True,
                "period_days": days,
                "trends": dict(by_date),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting trending emotions: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Create global controller instance
analytics_controller = AnalyticsController()

