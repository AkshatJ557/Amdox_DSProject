"""
Stress calculation and analysis service
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


class StressService:
    """
    Service for calculating and analyzing stress levels
    """
    
    def __init__(self):
        self.stress_emotions = ['Sad', 'Angry', 'Fear', 'Disgust']
        self.neutral_emotions = ['Neutral', 'Happy', 'Surprise']
        self.stress_levels = {
            'Low': (0, 2),
            'Moderate': (3, 5),
            'High': (6, 7),
            'Very High': (8, 10)
        }
        self.db = db_manager.get_database()
    
    def get_stress_level(self, score: int) -> str:
        """Get stress level label from score"""
        for level, (low, high) in self.stress_levels.items():
            if low <= score <= high:
                return level
        return 'Very High' if score > 7 else 'Low'
    
    def calculate_stress_score(
        self, 
        dominant_emotion: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Calculate stress score based on dominant emotion
        
        Args:
            dominant_emotion: The detected dominant emotion
            user_id: User ID for context
        
        Returns:
            dict: Stress analysis results
        """
        try:
            stress_score = 0
            
            # Base stress from emotion
            if dominant_emotion in ['Angry', 'Disgust']:
                stress_score = 8
            elif dominant_emotion == 'Fear':
                stress_score = 7
            elif dominant_emotion == 'Sad':
                stress_score = 6
            elif dominant_emotion == 'Neutral':
                stress_score = 4
            elif dominant_emotion == 'Surprise':
                stress_score = 3
            elif dominant_emotion == 'Happy':
                stress_score = 1
            
            # Get stress level
            stress_level = self.get_stress_level(stress_score)
            
            return {
                "success": True,
                "user_id": user_id,
                "dominant_emotion": dominant_emotion,
                "stress_score": stress_score,
                "stress_level": stress_level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error calculating stress score: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
            dict: Stress pattern analysis
        """
        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_stress": {"$avg": "$stress_score"},
                        "max_stress": {"$max": "$stress_score"},
                        "min_stress": {"$min": "$stress_score"},
                        "entry_count": {"$sum": 1},
                        "stress_scores": {"$push": "$stress_score"}
                    }
                }
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            if not results:
                return {
                    "success": True,
                    "message": "No stress data available for the specified period",
                    "analysis": {
                        "avg_stress": 0,
                        "max_stress": 0,
                        "min_stress": 0,
                        "entry_count": 0,
                        "trend": "unknown"
                    }
                }
            
            result = results[0]
            
            # Calculate trend
            trend = "stable"
            scores = result["stress_scores"]
            if len(scores) >= 7:
                first_week_avg = sum(scores[:7]) / 7
                last_week_avg = sum(scores[-7:]) / 7
                
                if last_week_avg > first_week_avg + 1:
                    trend = "increasing"
                elif last_week_avg < first_week_avg - 1:
                    trend = "decreasing"
            
            # Identify high stress periods
            high_stress_days = []
            if len(scores) > 0:
                avg = result["avg_stress"]
                if avg > 6:
                    high_stress_days = [
                        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
                    ]
            
            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "analysis": {
                    "avg_stress": round(result["avg_stress"], 2),
                    "max_stress": result["max_stress"],
                    "min_stress": result["min_stress"],
                    "entry_count": result["entry_count"],
                    "trend": trend,
                    "high_stress_days": high_stress_days,
                    "overall_level": self.get_stress_level(result["avg_stress"])
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error analyzing stress patterns: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_stress_threshold(
        self, 
        score: int, 
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Check if stress score crosses threshold
        
        Args:
            score: Stress score
            user_id: Optional user ID for context
        
        Returns:
            dict: Threshold check results
        """
        try:
            threshold = 7
            crossed = score >= threshold
            
            return {
                "success": True,
                "stress_score": score,
                "threshold": threshold,
                "threshold_crossed": crossed,
                "level": self.get_stress_level(score),
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error checking stress threshold: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stress_history(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get stress history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of entries
        
        Returns:
            dict: Stress history
        """
        try:
            collection = db_manager.get_collection("mood_entries")
            
            entries = list(
                collection
                .find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            history = []
            for entry in entries:
                history.append({
                    "timestamp": entry.get("timestamp", datetime.utcnow()).isoformat(),
                    "dominant_emotion": entry.get("dominant_emotion", "Unknown"),
                    "stress_score": entry.get("stress_score", 0),
                    "stress_level": self.get_stress_level(entry.get("stress_score", 0)),
                    "session_id": entry.get("session_id", "N/A")
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "entry_count": len(history),
                "history": history,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting stress history: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Create global service instance
stress_service = StressService()

