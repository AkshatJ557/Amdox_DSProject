"""
Enhanced Aggregation Service for Amdox
Production-grade data aggregation with MongoDB pipelines for team analytics
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict

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


class AggregationService:
    """
    Enhanced Aggregation Service for team and user analytics
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        logger.info("📊 Aggregation Service initialized")
    
    def aggregate_team_stress(
        self,
        team_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate stress data for a team
        
        Args:
            team_id: Optional team ID (None for all teams)
            days: Number of days to analyze
        
        Returns:
            dict: Aggregated stress data
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Build match stage
            match_stage = {"timestamp": {"$gte": since}}
            
            # Get team members if team_id provided
            user_ids = None
            if team_id:
                team = self.db.teams.find_one({"team_id": team_id})
                if not team:
                    return {
                        "success": False,
                        "error": f"Team {team_id} not found"
                    }
                user_ids = team.get("members", [])
                if user_ids:
                    match_stage["user_id"] = {"$in": user_ids}
            
            # Aggregation pipeline
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": None,
                        "overall_avg_stress": {"$avg": "$stress_score"},
                        "max_stress": {"$max": "$stress_score"},
                        "min_stress": {"$min": "$stress_score"},
                        "total_entries": {"$sum": 1},
                        "high_stress_count": {
                            "$sum": {"$cond": [{"$gte": ["$stress_score", 7]}, 1, 0]}
                        },
                        "moderate_stress_count": {
                            "$sum": {"$cond": [
                                {"$and": [
                                    {"$gte": ["$stress_score", 3]},
                                    {"$lt": ["$stress_score", 7]}
                                ]},
                                1,
                                0
                            ]}
                        },
                        "low_stress_count": {
                            "$sum": {"$cond": [{"$lt": ["$stress_score", 3]}, 1, 0]}
                        }
                    }
                }
            ]
            
            result = list(self.db.mood_entries.aggregate(pipeline))
            
            if not result or result[0]["_id"] is None:
                return {
                    "success": True,
                    "team_id": team_id,
                    "message": "No data available",
                    "data": {}
                }
            
            data = result[0]
            total = data["total_entries"]
            
            return {
                "success": True,
                "team_id": team_id,
                "period_days": days,
                "data": {
                    "overall_avg_stress": round(data["overall_avg_stress"], 2),
                    "max_stress": data["max_stress"],
                    "min_stress": data["min_stress"],
                    "total_entries": total,
                    "stress_distribution": {
                        "high": data["high_stress_count"],
                        "moderate": data["moderate_stress_count"],
                        "low": data["low_stress_count"]
                    },
                    "stress_distribution_percentage": {
                        "high": round((data["high_stress_count"] / total) * 100, 1) if total > 0 else 0,
                        "moderate": round((data["moderate_stress_count"] / total) * 100, 1) if total > 0 else 0,
                        "low": round((data["low_stress_count"] / total) * 100, 1) if total > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error aggregating team stress: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def aggregate_emotion_distribution(
        self,
        team_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate emotion distribution for team or system
        
        Args:
            team_id: Optional team ID
            days: Number of days to analyze
        
        Returns:
            dict: Emotion distribution data
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            match_stage = {"timestamp": {"$gte": since}}
            
            # Filter by team
            if team_id:
                team = self.db.teams.find_one({"team_id": team_id})
                if team and team.get("members"):
                    match_stage["user_id"] = {"$in": team["members"]}
            
            # Aggregation pipeline
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$dominant_emotion",
                        "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            if not results:
                return {
                    "success": True,
                    "message": "No emotion data available",
                    "distribution": {}
                }
            
            # Calculate total and percentages
            total = sum(r["count"] for r in results)
            
            distribution = {}
            for r in results:
                emotion = r["_id"]
                distribution[emotion] = {
                    "count": r["count"],
                    "percentage": round((r["count"] / total) * 100, 1) if total > 0 else 0,
                    "avg_confidence": round(r.get("avg_confidence", 0), 3)
                }
            
            return {
                "success": True,
                "team_id": team_id,
                "period_days": days,
                "distribution": distribution,
                "total_entries": total,
                "dominant_emotion": results[0]["_id"] if results else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"❌ Error aggregating emotion distribution: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def aggregate_user_activity(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate user activity across system
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: User activity data
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Pipeline for active users
            pipeline = [
                {"$match": {"timestamp": {"$gte": since}}},
                {
                    "$group": {
                        "_id": "$user_id",
                        "entry_count": {"$sum": 1},
                        "avg_stress": {"$avg": "$stress_score"},
                        "last_activity": {"$max": "$timestamp"}
                    }
                },
                {"$sort": {"entry_count": -1}}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            # Statistics
            total_users = len(results)
            total_entries = sum(r["entry_count"] for r in results)
            
            # Active users (>= 5 entries)
            active_users = [r for r in results if r["entry_count"] >= 5]
            
            # High stress users
            high_stress_users = [
                r for r in results 
                if r.get("avg_stress", 0) >= 7
            ]
            
            return {
                "success": True,
                "period_days": days,
                "statistics": {
                    "total_users": total_users,
                    "total_entries": total_entries,
                    "avg_entries_per_user": round(total_entries / total_users, 1) if total_users > 0 else 0,
                    "active_users_count": len(active_users),
                    "high_stress_users_count": len(high_stress_users)
                },
                "top_active_users": [
                    {
                        "user_id": r["_id"],
                        "entry_count": r["entry_count"],
                        "avg_stress": round(r["avg_stress"], 2),
                        "last_activity": r["last_activity"].isoformat()
                    }
                    for r in results[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error aggregating user activity: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_team_report(
        self,
        team_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive team report
        
        Args:
            team_id: Team ID
            days: Number of days to analyze
        
        Returns:
            dict: Comprehensive team report
        """
        try:
            logger.info(f"📊 Generating team report for {team_id}")
            
            # Get team info
            team = self.db.teams.find_one({"team_id": team_id})
            
            if not team:
                return {
                    "success": False,
                    "error": f"Team {team_id} not found"
                }
            
            # Get all data
            stress_data = self.aggregate_team_stress(team_id, days)
            emotion_data = self.aggregate_emotion_distribution(team_id, days)
            
            # Get member details
            member_ids = team.get("members", [])
            members = []
            
            for user_id in member_ids:
                # Get user stress stats
                user_stats = self._get_user_stress_stats(user_id, days)
                members.append(user_stats)
            
            # Sort members by avg stress
            members.sort(key=lambda x: x.get("avg_stress", 0), reverse=True)
            
            # Generate recommendations
            recommendations = self._generate_team_recommendations(
                stress_data.get("data", {}),
                emotion_data.get("distribution", {}),
                members
            )
            
            return {
                "success": True,
                "team_id": team_id,
                "team_name": team.get("name"),
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "overview": {
                    "member_count": len(members),
                    "overall_avg_stress": stress_data.get("data", {}).get("overall_avg_stress", 0),
                    "dominant_emotion": emotion_data.get("dominant_emotion", "Unknown"),
                    "high_stress_members": sum(1 for m in members if m.get("avg_stress", 0) >= 7)
                },
                "stress_analysis": stress_data.get("data", {}),
                "emotion_analysis": emotion_data.get("distribution", {}),
                "members": members,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating team report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_user_stress_stats(
        self,
        user_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Get stress statistics for a user"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": since}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_stress": {"$avg": "$stress_score"},
                        "max_stress": {"$max": "$stress_score"},
                        "entry_count": {"$sum": 1},
                        "dominant_emotions": {"$push": "$dominant_emotion"}
                    }
                }
            ]
            
            result = list(self.db.mood_entries.aggregate(pipeline))
            
            if not result or result[0]["_id"] is None:
                return {
                    "user_id": user_id,
                    "avg_stress": 0,
                    "max_stress": 0,
                    "entry_count": 0
                }
            
            data = result[0]
            
            # Get most common emotion
            from collections import Counter
            emotion_counter = Counter(data.get("dominant_emotions", []))
            most_common = emotion_counter.most_common(1)
            
            return {
                "user_id": user_id,
                "avg_stress": round(data.get("avg_stress", 0), 2),
                "max_stress": data.get("max_stress", 0),
                "entry_count": data.get("entry_count", 0),
                "most_common_emotion": most_common[0][0] if most_common else "Unknown"
            }
            
        except Exception:
            return {
                "user_id": user_id,
                "avg_stress": 0,
                "entry_count": 0
            }
    
    def _generate_team_recommendations(
        self,
        stress_data: Dict,
        emotion_data: Dict,
        members: List[Dict]
    ) -> List[str]:
        """Generate team-level recommendations"""
        recommendations = []
        
        try:
            avg_stress = stress_data.get("overall_avg_stress", 0)
            high_stress_count = stress_data.get("stress_distribution", {}).get("high", 0)
            
            # Stress-based recommendations
            if avg_stress >= 7:
                recommendations.append("🚨 URGENT: Team stress is critically high - immediate intervention needed")
                recommendations.append("📅 Schedule team wellness session")
                recommendations.append("📊 Review workload distribution across team")
            elif avg_stress >= 5:
                recommendations.append("⚠️ Elevated team stress - monitor closely")
                recommendations.append("💡 Consider flexible work arrangements")
                recommendations.append("🤝 Increase 1-on-1 check-ins")
            elif avg_stress <= 3:
                recommendations.append("✅ Team stress is well-managed")
                recommendations.append("🌟 Maintain current wellness practices")
            
            # Member-specific
            high_stress_members = [m for m in members if m.get("avg_stress", 0) >= 7]
            if high_stress_members:
                recommendations.append(
                    f"👥 {len(high_stress_members)} team member(s) with high stress - provide individual support"
                )
            
            # Emotion-based
            if emotion_data:
                total = sum(d.get("count", 0) for d in emotion_data.values())
                negative_count = sum(
                    emotion_data.get(e, {}).get("count", 0)
                    for e in ['Sad', 'Angry', 'Fear', 'Disgust']
                )
                
                if total > 0 and (negative_count / total) > 0.4:
                    recommendations.append("😔 High negative emotion prevalence - address team morale")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations if recommendations else ["Team appears to be functioning well"]
    
    def analyze_stress_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze stress patterns for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            dict: Pattern analysis
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            entries = list(
                self.db.mood_entries.find({
                    "user_id": user_id,
                    "timestamp": {"$gte": since}
                }).sort("timestamp", 1)
            )
            
            if not entries:
                return {
                    "success": True,
                    "message": "No data available",
                    "analysis": {}
                }
            
            stress_scores = [e.get("stress_score", 0) for e in entries]
            
            # Calculate statistics
            import numpy as np
            
            avg_stress = np.mean(stress_scores)
            std_stress = np.std(stress_scores)
            
            # Determine trend
            if len(stress_scores) >= 2:
                first_half = stress_scores[:len(stress_scores)//2]
                second_half = stress_scores[len(stress_scores)//2:]
                
                first_avg = np.mean(first_half)
                second_avg = np.mean(second_half)
                
                if second_avg > first_avg + 1:
                    trend = "increasing"
                elif second_avg < first_avg - 1:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"
            
            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "analysis": {
                    "avg_stress": round(avg_stress, 2),
                    "std_deviation": round(std_stress, 2),
                    "trend": trend,
                    "volatility": "high" if std_stress > 2 else "moderate" if std_stress > 1 else "low",
                    "total_entries": len(entries)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing stress patterns: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_overview(self, days: int = 7) -> Dict[str, Any]:
        """
        Get system-wide overview
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: System overview
        """
        try:
            stress_data = self.aggregate_team_stress(None, days)
            emotion_data = self.aggregate_emotion_distribution(None, days)
            activity_data = self.aggregate_user_activity(days)
            
            return {
                "success": True,
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "overview": {
                    "total_users": activity_data.get("statistics", {}).get("total_users", 0),
                    "total_entries": activity_data.get("statistics", {}).get("total_entries", 0),
                    "avg_stress": stress_data.get("data", {}).get("overall_avg_stress", 0),
                    "dominant_emotion": emotion_data.get("dominant_emotion", "Unknown")
                },
                "stress_breakdown": stress_data.get("data", {}),
                "emotion_breakdown": emotion_data.get("distribution", {}),
                "activity_stats": activity_data.get("statistics", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system overview: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Create global service instance
aggregation_service = AggregationService()