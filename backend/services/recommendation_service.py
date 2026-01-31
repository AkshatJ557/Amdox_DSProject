"""
Recommendation service for task suggestions based on emotion and context
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

from backend.config import (
    EMOTION_WEIGHTS,
    TASK_RECOMMENDATIONS,
    STRESS_LEVELS,
    get_stress_level
)


class RecommendationService:
    """
    Service for generating task recommendations based on emotion and context
    """
    
    def __init__(self):
        self.emotion_weights = EMOTION_WEIGHTS
        self.task_recommendations = TASK_RECOMMENDATIONS
        self.stress_levels = STRESS_LEVELS
    
    def recommend_task(
        self, 
        dominant_emotion: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a task recommendation based on dominant emotion
        
        Args:
            dominant_emotion: The detected dominant emotion
            context: Optional context (stress_score, workload_level, etc.)
        
        Returns:
            dict: Task recommendation
        """
        try:
            emotion_config = self.task_recommendations.get(
                dominant_emotion, 
                self.task_recommendations['Neutral']
            )
            
            tasks = emotion_config.get('tasks', [])
            if not tasks:
                task = "Take a short break"
            else:
                task = tasks[0]
            
            stress_score = context.get('stress_score', 0) if context else 0
            stress_level = get_stress_level(stress_score)
            
            # Adjust priority based on stress
            if stress_score >= 7:
                priority = "High"
                duration = "10-15 minutes"
            elif stress_score >= 4:
                priority = "Medium-High"
                duration = "20-30 minutes"
            else:
                priority = emotion_config.get('priority', 'Medium')
                duration = emotion_config.get('duration', '30-45 minutes')
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(dominant_emotion, context)
            
            return {
                "success": True,
                "dominant_emotion": dominant_emotion,
                "recommendation": {
                    "task": task,
                    "category": emotion_config.get('category', 'General'),
                    "priority": priority,
                    "duration": duration,
                    "confidence_score": confidence_score
                },
                "stress_context": {
                    "stress_score": stress_score,
                    "stress_level": stress_level
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
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
            emotion_config = self.task_recommendations.get(
                dominant_emotion, 
                self.task_recommendations['Neutral']
            )
            
            tasks = emotion_config.get('tasks', [])
            
            suggestions = []
            for i, task in enumerate(tasks[:count]):
                suggestions.append({
                    "task": task,
                    "category": emotion_config.get('category', 'General'),
                    "priority": emotion_config.get('priority', 'Medium'),
                    "index": i + 1
                })
            
            if not suggestions:
                suggestions = [
                    {"task": "Take a short break", "category": "General", "priority": "Medium", "index": 1}
                ]
            
            return {
                "success": True,
                "dominant_emotion": dominant_emotion,
                "suggestions": suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
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
            emotion_task_mapping = {}
            
            for emotion, config in self.task_recommendations.items():
                emotion_task_mapping[emotion] = {
                    "category": config.get('category', 'General'),
                    "tasks": config.get('tasks', []),
                    "priority": config.get('priority', 'Medium'),
                    "duration": config.get('duration', '30-45 minutes')
                }
            
            return {
                "success": True,
                "emotion_task_mapping": emotion_task_mapping,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting emotion-based tasks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_confidence(
        self, 
        dominant_emotion: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate confidence score for recommendation
        
        Args:
            dominant_emotion: The detected dominant emotion
            context: Optional context
        
        Returns:
            float: Confidence score between 0 and 1
        """
        try:
            base_confidence = 0.7
            
            # Boost confidence if context is provided
            if context:
                if context.get('stress_score') is not None:
                    base_confidence += 0.1
                if context.get('workload_level') is not None:
                    base_confidence += 0.05
                if context.get('deadline_pressure') is not None:
                    base_confidence += 0.05
                if context.get('sleep_hours') is not None:
                    base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception:
            return 0.6
    
    def get_recommendation_for_stress(
        self, 
        stress_score: int, 
        stress_level: str
    ) -> Dict[str, Any]:
        """
        Get a recommendation specifically for stress relief
        
        Args:
            stress_score: Current stress score
            stress_level: Stress level label
        
        Returns:
            dict: Stress relief recommendation
        """
        try:
            if stress_level == 'Very High':
                return {
                    "success": True,
                    "recommendation": {
                        "task": "Immediate break required - step away from work",
                        "category": "Emergency",
                        "priority": "Critical",
                        "duration": "15-30 minutes",
                        "type": "stress_relief"
                    }
                }
            elif stress_level == 'High':
                return {
                    "success": True,
                    "recommendation": {
                        "task": "Practice deep breathing and take a walk",
                        "category": "Stress Relief",
                        "priority": "High",
                        "duration": "10-15 minutes",
                        "type": "stress_relief"
                    }
                }
            elif stress_level == 'Moderate':
                return {
                    "success": True,
                    "recommendation": {
                        "task": "Quick meditation session",
                        "category": "Stress Relief",
                        "priority": "Medium",
                        "duration": "5-10 minutes",
                        "type": "stress_relief"
                    }
                }
            else:
                return {
                    "success": True,
                    "recommendation": {
                        "task": "Continue current workflow",
                        "category": "Maintenance",
                        "priority": "Low",
                        "duration": "N/A",
                        "type": "maintenance"
                    }
                }
                
        except Exception as e:
            print(f"❌ Error getting stress recommendation: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Create global service instance
recommendation_service = RecommendationService()

