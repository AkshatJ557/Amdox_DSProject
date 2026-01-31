"""
Enhanced Stress Service for Amdox - ALIGNED WITH NOTEBOOK LOGIC
Production-grade stress calculation using 5-factor algorithm from notebook
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


class StressService:
    """
    Enhanced Stress Service with notebook-aligned 5-factor calculation
    Algorithm from: Amdox_Model.ipynb Cell 7
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        logger.info("💊 Stress Service initialized (Notebook-aligned)")
    
    def calculate_stress_score(
        self,
        dominant_emotion: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate stress score using notebook's 5-factor algorithm
        
        Factors (each 0-10 points, total max 50):
        1. Mood (emotion)
        2. Current Workload
        3. Deadline Pressure  
        4. Working Hours
        5. Sleeping Hours
        
        Final Score = Total Points / 5.0 → (0-10 scale)
        
        Args:
            dominant_emotion: Detected emotion
            user_id: User ID
            context: Additional factors (workload, sleep, etc.)
        
        Returns:
            dict: Stress score with breakdown
        """
        try:
            points = 0.0
            max_points = 50.0
            factor_breakdown = {}
            
            # ===== FACTOR 1: MOOD SCORING (0-10 points) =====
            # From notebook Cell 7
            mood_points_map = {
                'Happy': 0.0,
                'Surprise': 2.5,
                'Neutral': 5.0,
                'Sad': 7.5,
                'Fear': 7.5,
                'Disgust': 7.5,
                'Angry': 10.0
            }
            
            mood_points = mood_points_map.get(dominant_emotion, 5.0)
            points += mood_points
            factor_breakdown['mood'] = {
                'value': dominant_emotion,
                'points': mood_points,
                'max_points': 10.0
            }
            
            # ===== FACTOR 2-5: CONTEXT-BASED (if provided) =====
            if context:
                # FACTOR 2: WORKLOAD (0-10 points)
                workload = context.get('workload_level', context.get('current_workload', None))
                if workload is not None:
                    workload_points = self._calculate_workload_points(workload)
                    points += workload_points
                    factor_breakdown['workload'] = {
                        'value': workload,
                        'points': workload_points,
                        'max_points': 10.0
                    }
                
                # FACTOR 3: DEADLINE PRESSURE (0-10 points)
                deadline = context.get('deadline_pressure', None)
                if deadline is not None:
                    deadline_points = self._calculate_deadline_points(deadline)
                    points += deadline_points
                    factor_breakdown['deadline_pressure'] = {
                        'value': deadline,
                        'points': deadline_points,
                        'max_points': 10.0
                    }
                
                # FACTOR 4: WORKING HOURS (0-10 points)
                work_hours = context.get('working_hours', None)
                if work_hours is not None:
                    work_hours_points = self._calculate_work_hours_points(work_hours)
                    points += work_hours_points
                    factor_breakdown['working_hours'] = {
                        'value': work_hours,
                        'points': work_hours_points,
                        'max_points': 10.0
                    }
                
                # FACTOR 5: SLEEPING HOURS (0-10 points, optimal 8-9)
                sleep_hours = context.get('sleep_hours', context.get('sleeping_hours', None))
                if sleep_hours is not None:
                    sleep_points = self._calculate_sleep_points(sleep_hours)
                    points += sleep_points
                    factor_breakdown['sleeping_hours'] = {
                        'value': sleep_hours,
                        'points': sleep_points,
                        'max_points': 10.0
                    }
            
            # ===== NORMALIZE TO 0-10 SCALE =====
            # If only mood available: use mood points directly (already 0-10)
            # If multiple factors: normalize total points
            factors_used = len(factor_breakdown)
            
            if factors_used == 1:
                # Only mood - use direct mapping
                final_score = mood_points
            else:
                # Multiple factors - normalize
                final_score = points / 5.0
            
            # Ensure within bounds
            final_score = max(0, min(10, final_score))
            stress_score_int = int(round(final_score))
            
            # Get stress level
            stress_level = self.get_stress_level(stress_score_int)
            
            # Determine if threshold crossed
            threshold_crossed = stress_score_int >= 7
            moderate_threshold = stress_score_int >= 3
            
            result = {
                "success": True,
                "stress_score": stress_score_int,
                "stress_score_precise": round(final_score, 2),
                "stress_level": stress_level,
                "raw_points": round(points, 2),
                "max_possible_points": max_points,
                "factors_used": factors_used,
                "factor_breakdown": factor_breakdown,
                "thresholds": {
                    "moderate_crossed": moderate_threshold,
                    "high_crossed": threshold_crossed,
                    "moderate_threshold": 3,
                    "high_threshold": 7
                },
                "calculation_method": "notebook_5_factor" if factors_used > 1 else "emotion_only"
            }
            
            logger.debug(
                f"💊 Stress calculated: {stress_score_int}/10 ({stress_level}) "
                f"for {user_id} using {factors_used} factors"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calculating stress: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _calculate_workload_points(self, workload: int) -> float:
        """
        Calculate workload stress points (0-10 scale input)
        From notebook: Bins workload into 5 categories
        
        0-2: Very Low (0 pts)
        3-4: Low (2.5 pts)
        5-6: Moderate (5 pts)
        7-8: High (7.5 pts)
        9-10: Very High (10 pts)
        """
        if workload <= 2:
            return 0.0
        elif workload <= 4:
            return 2.5
        elif workload <= 6:
            return 5.0
        elif workload <= 8:
            return 7.5
        else:
            return 10.0
    
    def _calculate_deadline_points(self, deadline: int) -> float:
        """
        Calculate deadline pressure points (0-10 scale input)
        Same bins as workload
        """
        if deadline <= 2:
            return 0.0
        elif deadline <= 4:
            return 2.5
        elif deadline <= 6:
            return 5.0
        elif deadline <= 8:
            return 7.5
        else:
            return 10.0
    
    def _calculate_work_hours_points(self, hours: float) -> float:
        """
        Calculate working hours stress points
        
        0-4: Minimal (0 pts)
        5-7: Standard (2.5 pts)
        8-10: High (5 pts)
        11-13: Very High (7.5 pts)
        14+: Extreme (10 pts)
        """
        if hours <= 4:
            return 0.0
        elif hours <= 7:
            return 2.5
        elif hours <= 10:
            return 5.0
        elif hours <= 13:
            return 7.5
        else:
            return 10.0
    
    def _calculate_sleep_points(self, hours: float) -> float:
        """
        Calculate sleep hours stress points
        Optimal is 8-9 hours
        
        8-9: Optimal (0 pts)
        7 or 10: Good (2.5 pts)
        6 or 11: Fair (5 pts)
        5 or 12: Poor (7.5 pts)
        <5 or >12: Critical (10 pts)
        """
        if 8 <= hours <= 9:
            return 0.0
        elif hours == 7 or hours == 10:
            return 2.5
        elif hours == 6 or hours == 11:
            return 5.0
        elif hours == 5 or hours == 12:
            return 7.5
        else:
            return 10.0
    
    def get_stress_level(self, score: int) -> str:
        """
        Get stress level label from score
        
        Args:
            score: Stress score (0-10)
        
        Returns:
            str: Stress level label
        """
        if score <= 2:
            return "Very Low"
        elif score <= 5:
            return "Moderate"
        elif score <= 7:
            return "High"
        else:
            return "Very High"
    
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
            mood_collection = self.db.mood_entries
            
            entries = list(
                mood_collection
                .find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            history = []
            for entry in entries:
                history.append({
                    "timestamp": entry.get("timestamp").isoformat() if entry.get("timestamp") else None,
                    "stress_score": entry.get("stress_score", 0),
                    "dominant_emotion": entry.get("dominant_emotion", "Unknown"),
                    "session_id": entry.get("session_id")
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "history": history,
                "count": len(history)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stress history: {e}", exc_info=True)
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
        Analyze stress patterns over time
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            dict: Stress pattern analysis
        """
        try:
            mood_collection = self.db.mood_entries
            
            since = datetime.utcnow() - timedelta(days=days)
            
            entries = list(
                mood_collection.find({
                    "user_id": user_id,
                    "timestamp": {"$gte": since}
                }).sort("timestamp", 1)
            )
            
            if not entries:
                return {
                    "success": True,
                    "message": "No data available for analysis",
                    "analysis": {}
                }
            
            # Extract stress scores
            stress_scores = [e.get("stress_score", 0) for e in entries]
            
            # Calculate statistics
            import numpy as np
            
            avg_stress = np.mean(stress_scores)
            max_stress = np.max(stress_scores)
            min_stress = np.min(stress_scores)
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
                trend = "insufficient_data"
            
            # Count high stress events
            high_stress_events = sum(1 for s in stress_scores if s >= 7)
            moderate_stress_events = sum(1 for s in stress_scores if 3 <= s < 7)
            
            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "analysis": {
                    "avg_stress": round(avg_stress, 2),
                    "max_stress": int(max_stress),
                    "min_stress": int(min_stress),
                    "std_deviation": round(std_stress, 2),
                    "trend": trend,
                    "high_stress_events": high_stress_events,
                    "moderate_stress_events": moderate_stress_events,
                    "total_entries": len(stress_scores),
                    "high_stress_percentage": round(
                        (high_stress_events / len(stress_scores)) * 100, 1
                    ) if stress_scores else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing stress patterns: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_stress_threshold(
        self,
        score: int,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if stress score crosses thresholds
        
        Args:
            score: Stress score
            user_id: Optional user ID
        
        Returns:
            dict: Threshold check results
        """
        try:
            result = {
                "success": True,
                "score": score,
                "level": self.get_stress_level(score),
                "thresholds": {
                    "moderate": {
                        "value": 3,
                        "crossed": score >= 3,
                        "description": "Moderate stress - monitor closely"
                    },
                    "high": {
                        "value": 7,
                        "crossed": score >= 7,
                        "description": "High stress - intervention needed"
                    },
                    "critical": {
                        "value": 9,
                        "crossed": score >= 9,
                        "description": "Critical stress - immediate action required"
                    }
                }
            }
            
            # Add recommendations based on threshold
            if score >= 9:
                result["alert_level"] = "critical"
                result["action_required"] = "immediate"
            elif score >= 7:
                result["alert_level"] = "high"
                result["action_required"] = "urgent"
            elif score >= 3:
                result["alert_level"] = "moderate"
                result["action_required"] = "monitor"
            else:
                result["alert_level"] = "low"
                result["action_required"] = "none"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking threshold: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recommendation_for_stress(
        self,
        stress_score: int,
        stress_level: str
    ) -> Dict[str, Any]:
        """
        Get recommendations based on stress level
        
        Args:
            stress_score: Stress score
            stress_level: Stress level label
        
        Returns:
            dict: Recommendations
        """
        try:
            recommendations = []
            
            if stress_score >= 9:
                recommendations = [
                    "🚨 URGENT: Take immediate break from all tasks",
                    "💬 Contact your manager or HR immediately",
                    "🧘 Practice deep breathing exercises (4-7-8 technique)",
                    "🏥 Consider professional counseling support",
                    "📱 Reach out to someone you trust"
                ]
            elif stress_score >= 7:
                recommendations = [
                    "⚠️ Take a 15-20 minute break immediately",
                    "🚶 Go for a short walk outside",
                    "💭 Practice mindfulness meditation",
                    "💬 Speak with your team lead about workload",
                    "📝 Write down your concerns to clear your mind"
                ]
            elif stress_score >= 5:
                recommendations = [
                    "☕ Take regular short breaks",
                    "🎵 Listen to calming music",
                    "💪 Do light stretching exercises",
                    "📊 Prioritize and organize your tasks",
                    "😌 Practice relaxation techniques"
                ]
            elif stress_score >= 3:
                recommendations = [
                    "✅ Maintain current stress management practices",
                    "⏰ Ensure regular breaks throughout the day",
                    "💤 Get adequate sleep (8-9 hours)",
                    "🏃 Consider light physical activity"
                ]
            else:
                recommendations = [
                    "🌟 Excellent stress levels!",
                    "✅ Continue with positive habits",
                    "📈 Keep tracking your wellness"
                ]
            
            return {
                "success": True,
                "stress_score": stress_score,
                "stress_level": stress_level,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting recommendations: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Create global service instance
stress_service = StressService()