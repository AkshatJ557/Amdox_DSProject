"""
Aggregation service for combining data from multiple sources
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager


class AggregationService:
    """
    Service for aggregating data from multiple sources
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.stress_levels = {
            'Low': (0, 2),
            'Moderate': (3, 5),
            'High': (6, 7),
            'Very High': (8, 10)
        }
    
    def get_stress_level(self, score: int) -> str:
        """Get stress level label from score"""
        for level, (low, high) in self.stress_levels.items():
            if low <= score <= high:
                return level
        return 'Very High' if score > 7 else 'Low'
    
    def aggregate_team_stress(
        self, 
        team_id: str = None, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate stress data for a team or entire organization
        
        Args:
            team_id: Optional team ID to filter by
            days: Number of days to analyze
        
        Returns:
            dict: Aggregated stress data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build match stage
            match_stage = {
                "timestamp": {"$gte": start_date}
            }
            if team_id:
                match_stage["team_id"] = team_id
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "user_id": "$user_id",
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                        },
                        "avg_stress": {"$avg": "$stress_score"},
                        "max_stress": {"$max": "$stress_score"},
                        "min_stress": {"$min": "$stress_score"},
                        "entry_count": {"$sum": 1}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "daily_averages": {
                            "$push": {
                                "date": "$_id.date",
                                "avg_stress": "$avg_stress",
                                "max_stress": "$max_stress",
                                "min_stress": "$min_stress",
                                "entries": "$entry_count"
                            }
                        },
                        "overall_avg_stress": {"$avg": "$avg_stress"},
                        "overall_max_stress": {"$max": "$max_stress"},
                        "team_size": {"$sum": 1}
                    }
                }
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            if not results:
                return {
                    "success": True,
                    "period_days": days,
                    "team_id": team_id,
                    "message": "No data available for the specified period",
                    "data": {
                        "daily_averages": [],
                        "overall_avg_stress": 0,
                        "overall_max_stress": 0,
                        "team_size": 0,
                        "stress_distribution": {}
                    }
                }
            
            result = results[0]
            
            # Calculate stress distribution
            stress_distribution = defaultdict(int)
            for day in result["daily_averages"]:
                level = self.get_stress_level(day["avg_stress"])
                stress_distribution[level] += 1
            
            return {
                "success": True,
                "period_days": days,
                "team_id": team_id,
                "data": {
                    "daily_averages": sorted(
                        result["daily_averages"], 
                        key=lambda x: x["date"]
                    ),
                    "overall_avg_stress": round(result["overall_avg_stress"], 2),
                    "overall_max_stress": result["overall_max_stress"],
                    "team_size": result["team_size"],
                    "stress_distribution": dict(stress_distribution)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error aggregating team stress: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def aggregate_emotion_distribution(
        self, 
        team_id: str = None, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate emotion distribution data
        
        Args:
            team_id: Optional team ID to filter by
            days: Number of days to analyze
        
        Returns:
            dict: Aggregated emotion distribution
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            match_stage = {"timestamp": {"$gte": start_date}}
            if team_id:
                match_stage["team_id"] = team_id
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "emotion": "$dominant_emotion",
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                        },
                        "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"}
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.emotion",
                        "total_count": {"$sum": "$count"},
                        "avg_confidence": {"$avg": "$avg_confidence"},
                        "daily_breakdown": {
                            "$push": {
                                "date": "$_id.date",
                                "count": "$count"
                            }
                        }
                    }
                },
                {"$sort": {"total_count": -1}}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            if not results:
                return {
                    "success": True,
                    "period_days": days,
                    "team_id": team_id,
                    "message": "No data available for the specified period",
                    "distribution": {}
                }
            
            distribution = {
                r["_id"]: {
                    "count": r["total_count"],
                    "percentage": 0,  # Will calculate below
                    "avg_confidence": round(r["avg_confidence"], 3),
                    "daily_breakdown": r["daily_breakdown"]
                }
                for r in results
            }
            
            total = sum(d["count"] for d in distribution.values())
            for emotion in distribution:
                distribution[emotion]["percentage"] = round(
                    (distribution[emotion]["count"] / total) * 100, 
                    2
                )
            
            return {
                "success": True,
                "period_days": days,
                "team_id": team_id,
                "total_entries": total,
                "distribution": distribution,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error aggregating emotion distribution: {e}")
            return {
                "success": False,
                "error": str(e),
                "distribution": None
            }
    
    def aggregate_session_data(
        self, 
        session_id: str = None, 
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Aggregate data for a specific session or user sessions
        
        Args:
            session_id: Optional session ID
            user_id: Optional user ID
        
        Returns:
            dict: Aggregated session data
        """
        try:
            match_stage = {}
            if session_id:
                match_stage["session_id"] = session_id
            if user_id:
                match_stage["user_id"] = user_id
            
            if not match_stage:
                return {
                    "success": False,
                    "error": "Either session_id or user_id must be provided"
                }
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$session_id",
                        "emotion_counts": {"$push": "$dominant_emotion"},
                        "stress_scores": {"$push": "$stress_score"},
                        "confidence_scores": {"$push": "$confidence"},
                        "timestamps": {"$push": "$timestamp"},
                        "user_id": {"$first": "$user_id"},
                        "entry_count": {"$sum": 1},
                        "avg_stress": {"$avg": "$stress_score"},
                        "avg_confidence": {"$avg": "$confidence"}
                    }
                }
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            if not results:
                return {
                    "success": True,
                    "message": "No session data found",
                    "sessions": []
                }
            
            sessions = []
            for r in results:
                from collections import Counter
                emotion_counter = Counter(r["emotion_counts"])
                
                sessions.append({
                    "session_id": r["_id"],
                    "user_id": r["user_id"],
                    "entry_count": r["entry_count"],
                    "emotion_distribution": dict(emotion_counter),
                    "dominant_emotion": emotion_counter.most_common(1)[0][0],
                    "avg_stress": round(r["avg_stress"], 2),
                    "avg_confidence": round(r["avg_confidence"], 3),
                    "duration_minutes": (
                        max(r["timestamps"]) - min(r["timestamps"])
                    ).total_seconds() / 60 if len(r["timestamps"]) > 1 else 0,
                    "start_time": min(r["timestamps"]).isoformat(),
                    "end_time": max(r["timestamps"]).isoformat()
                })
            
            return {
                "success": True,
                "session_count": len(sessions),
                "sessions": sessions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error aggregating session data: {e}")
            return {
                "success": False,
                "error": str(e),
                "sessions": None
            }
    
    def generate_team_report(
        self, 
        team_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive team report
        
        Args:
            team_id: Team ID
            days: Number of days to analyze
        
        Returns:
            dict: Comprehensive team report
        """
        try:
            stress_data = self.aggregate_team_stress(team_id, days)
            emotion_data = self.aggregate_emotion_distribution(team_id, days)
            
            return {
                "success": True,
                "report": {
                    "team_id": team_id,
                    "period_days": days,
                    "generated_at": datetime.utcnow().isoformat(),
                    "stress_analysis": stress_data.get("data", {}),
                    "emotion_distribution": emotion_data.get("distribution", {}),
                    "recommendations": self._generate_recommendations(
                        stress_data.get("data", {}),
                        emotion_data.get("distribution", {})
                    )
                }
            }
        except Exception as e:
            print(f"❌ Error generating team report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_recommendations(
        self, 
        stress_data: Dict, 
        emotion_data: Dict
    ) -> List[str]:
        """Generate recommendations based on aggregated data"""
        recommendations = []
        
        try:
            avg_stress = stress_data.get("overall_avg_stress", 0)
            if avg_stress > 6:
                recommendations.append(
                    "Team stress levels are high. Consider team-building activities."
                )
            elif avg_stress > 4:
                recommendations.append(
                    "Team stress is moderate. Monitor and offer support resources."
                )
            
            if emotion_data:
                negative_emotions = ['Angry', 'Sad', 'Fear', 'Disgust']
                total = sum(e.get("count", 0) for e in emotion_data.values())
                negative_count = sum(
                    emotion_data.get(e, {}).get("count", 0) 
                    for e in negative_emotions
                )
                
                if total > 0 and (negative_count / total) > 0.4:
                    recommendations.append(
                        "High proportion of negative emotions detected. "
                        "Consider wellness initiatives."
                    )
            
            if not recommendations:
                recommendations.append("Team is performing well. Keep up the good work!")
                
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            recommendations = ["Unable to generate recommendations."]
        
        return recommendations


# Create global service instance
aggregation_service = AggregationService()

