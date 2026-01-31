"""
Stress controller for stress-related endpoints
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

from backend.services.stress_service import stress_service
from backend.services.alert_service import alert_service


class StressController:
    """
    Controller for stress-related endpoints
    """
    
    def __init__(self):
        self.stress_service = stress_service
        self.alert_service = alert_service
    
    def calculate_stress(
        self, 
        dominant_emotion: str, 
        user_id: str,
        previous_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate stress score based on dominant emotion
        
        Args:
            dominant_emotion: The detected dominant emotion
            user_id: User ID
            previous_score: Optional previous stress score for comparison
        
        Returns:
            dict: Stress calculation result
        """
        try:
            # Calculate stress score
            result = self.stress_service.calculate_stress_score(dominant_emotion, user_id)
            
            if result["success"]:
                stress_score = result["stress_score"]
                stress_level = result["stress_level"]
                
                # Check if we should create an alert
                if stress_score >= 7:
                    alert_result = self.alert_service.check_and_create_alert(
                        user_id=user_id,
                        alert_type="high_stress",
                        severity="high",
                        message=f"High stress detected: {stress_level}",
                        metadata={
                            "stress_score": stress_score,
                            "dominant_emotion": dominant_emotion
                        }
                    )
                    result["alert_triggered"] = alert_result.get("alert_created", False)
                
                # Add comparison with previous score
                if previous_score is not None:
                    result["comparison"] = {
                        "previous_score": previous_score,
                        "current_score": stress_score,
                        "change": stress_score - previous_score,
                        "trend": "increasing" if stress_score > previous_score else "decreasing" if stress_score < previous_score else "stable"
                    }
            
            return result
            
        except Exception as e:
            print(f"❌ Error calculating stress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_stress_history(
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
            result = self.stress_service.get_stress_history(user_id, limit)
            return result
            
        except Exception as e:
            print(f"❌ Error getting stress history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stress_trend(
        self, 
        user_id: str, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get stress trend analysis for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            dict: Stress trend analysis
        """
        try:
            result = self.stress_service.analyze_stress_patterns(user_id, days)
            return result
            
        except Exception as e:
            print(f"❌ Error getting stress trend: {e}")
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
        Check if stress score crosses threshold
        
        Args:
            score: Stress score
            user_id: Optional user ID
        
        Returns:
            dict: Threshold check result
        """
        try:
            result = self.stress_service.check_stress_threshold(score, user_id)
            return result
            
        except Exception as e:
            print(f"❌ Error checking stress threshold: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stress_recommendation(
        self, 
        stress_score: int
    ) -> Dict[str, Any]:
        """
        Get stress relief recommendation
        
        Args:
            stress_score: Current stress score
        
        Returns:
            dict: Stress relief recommendation
        """
        try:
            from backend.config import get_stress_level
            
            stress_level = get_stress_level(stress_score)
            result = self.stress_service.get_recommendation_for_stress(
                stress_score, stress_level
            )
            return result
            
        except Exception as e:
            print(f"❌ Error getting stress recommendation: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Create global controller instance
stress_controller = StressController()

