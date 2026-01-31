"""
Recommendation controller for task recommendation endpoints
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

from backend.services.recommendation_service import recommendation_service


class RecommendationController:
    """
    Controller for recommendation endpoints
    """
    
    def __init__(self):
        self.recommendation_service = recommendation_service
    
    def recommend_task(
        self, 
        dominant_emotion: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get task recommendation based on emotion and context
        
        Args:
            dominant_emotion: The detected dominant emotion
            context: Optional context (stress_score, workload_level, etc.)
        
        Returns:
            dict: Task recommendation
        """
        try:
            result = self.recommendation_service.recommend_task(
                dominant_emotion=dominant_emotion,
                context=context
            )
            return result
            
        except Exception as e:
            print(f"❌ Error generating recommendation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_multiple_recommendations(
        self, 
        dominant_emotion: str, 
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Get multiple task suggestions for an emotion
        
        Args:
            dominant_emotion: The detected dominant emotion
            count: Number of suggestions to return
        
        Returns:
            dict: Multiple recommendations
        """
        try:
            result = self.recommendation_service.get_multiple_recommendations(
                dominant_emotion=dominant_emotion,
                count=count
            )
            return result
            
        except Exception as e:
            print(f"❌ Error getting multiple recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_emotion_based_tasks(self) -> Dict[str, Any]:
        """
        Get all available tasks organized by emotion
        
        Returns:
            dict: Emotion-task mapping
        """
        try:
            result = self.recommendation_service.get_emotion_based_tasks()
            return result
            
        except Exception as e:
            print(f"❌ Error getting emotion-based tasks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recommendation_with_context(
        self, 
        dominant_emotion: str,
        stress_score: Optional[int] = None,
        workload_level: Optional[int] = None,
        deadline_pressure: Optional[int] = None,
        sleep_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get recommendation with full context
        
        Args:
            dominant_emotion: The detected dominant emotion
            stress_score: Current stress score
            workload_level: Workload level (1-5)
            deadline_pressure: Deadline pressure (1-5)
            sleep_hours: Hours of sleep last night
        
        Returns:
            dict: Context-aware recommendation
        """
        try:
            context = {}
            if stress_score is not None:
                context["stress_score"] = stress_score
            if workload_level is not None:
                context["workload_level"] = workload_level
            if deadline_pressure is not None:
                context["deadline_pressure"] = deadline_pressure
            if sleep_hours is not None:
                context["sleep_hours"] = sleep_hours
            
            result = self.recommendation_service.recommend_task(
                dominant_emotion=dominant_emotion,
                context=context
            )
            
            # Add contextual insights
            if result["success"]:
                insights = self._generate_contextual_insights(context)
                result["contextual_insights"] = insights
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting contextual recommendation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_contextual_insights(self, context: Dict) -> Dict[str, Any]:
        """Generate insights based on context"""
        insights = {
            "factors_considered": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            if context.get("stress_score", 0) >= 7:
                insights["warnings"].append("High stress detected. Recommendations focus on stress relief.")
                insights["factors_considered"].append("stress_score")
            
            if context.get("workload_level", 0) >= 4:
                insights["warnings"].append("Heavy workload detected. Consider delegating or rescheduling tasks.")
                insights["factors_considered"].append("workload_level")
            
            if context.get("deadline_pressure", 0) >= 4:
                insights["warnings"].append("High deadline pressure. Focus on high-priority tasks only.")
                insights["factors_considered"].append("deadline_pressure")
            
            if context.get("sleep_hours", 8) < 6:
                insights["suggestions"].append("Low sleep detected. Consider a shorter, more focused work session.")
                insights["factors_considered"].append("sleep_hours")
            
            if not insights["warnings"]:
                insights["suggestions"].append("Current context appears favorable for focused work.")
            
        except Exception as e:
            print(f"❌ Error generating contextual insights: {e}")
        
        return insights


# Create global controller instance
recommendation_controller = RecommendationController()

