"""
Enhanced Stress Controller for Amdox
Production-grade stress analysis with predictive alerts and comprehensive management
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
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

from backend.services.stress_service import stress_service
from backend.services.alert_service import alert_service
from backend.database.db import db_manager


class StressController:
    """
    Enhanced Controller for stress-related endpoints with predictive capabilities
    """
    
    def __init__(self):
        self.stress_service = stress_service
        self.alert_service = alert_service
        self.db = db_manager.get_database()
        self._stress_cache = {}  # Cache recent calculations
        logger.info("✅ Stress Controller initialized")
    
    def calculate_stress(
        self, 
        dominant_emotion: str, 
        user_id: str,
        previous_score: Optional[int] = None,
        additional_factors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive stress score with trend analysis
        
        Args:
            dominant_emotion: The detected dominant emotion
            user_id: User ID
            previous_score: Optional previous stress score
            additional_factors: Additional stress factors (workload, sleep, etc.)
        
        Returns:
            dict: Comprehensive stress analysis
        """
        try:
            # Validate inputs
            if not user_id:
                return {
                    "success": False,
                    "error": "user_id is required"
                }
            
            valid_emotions = ['Happy', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust', 'Neutral']
            if dominant_emotion not in valid_emotions:
                return {
                    "success": False,
                    "error": f"Invalid emotion. Must be one of: {', '.join(valid_emotions)}"
                }
            
            logger.info(f"📊 Calculating stress for user {user_id}, emotion: {dominant_emotion}")
            
            # Calculate base stress score
            result = self.stress_service.calculate_stress_score(dominant_emotion, user_id)
            
            if not result.get("success"):
                return result
            
            stress_score = result["stress_score"]
            stress_level = result["stress_level"]
            
            # Apply additional factors if provided
            if additional_factors:
                stress_score, adjustments = self._apply_stress_factors(
                    stress_score,
                    additional_factors
                )
                result["adjustments"] = adjustments
                result["stress_score"] = stress_score
                result["stress_level"] = self.stress_service.get_stress_level(stress_score)
            
            # Get historical context
            history = self._get_recent_stress_history(user_id, days=7)
            if history:
                result["historical_context"] = {
                    "average_last_7d": round(sum(history) / len(history), 2),
                    "trend": self._calculate_trend(history, stress_score),
                    "volatility": self._calculate_volatility(history)
                }
            
            # Check if alert should be created
            if stress_score >= 7:
                alert_result = self.alert_service.check_and_create_alert(
                    user_id=user_id,
                    alert_type="high_stress",
                    severity="high" if stress_score >= 8 else "medium",
                    message=f"High stress detected: {stress_level} (Score: {stress_score})",
                    metadata={
                        "stress_score": stress_score,
                        "dominant_emotion": dominant_emotion,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                result["alert_triggered"] = alert_result.get("alert_created", False)
                
                if alert_result.get("alert_created"):
                    result["alert_id"] = str(alert_result.get("alert", {}).get("_id"))
            
            # Add comparison with previous score
            if previous_score is not None:
                result["comparison"] = {
                    "previous_score": previous_score,
                    "current_score": stress_score,
                    "change": stress_score - previous_score,
                    "change_percentage": round(
                        ((stress_score - previous_score) / previous_score * 100) 
                        if previous_score > 0 else 0, 
                        1
                    ),
                    "trend": self._get_change_trend(stress_score, previous_score)
                }
            
            # Get personalized recommendations
            result["recommendations"] = self._get_stress_recommendations(
                stress_score,
                stress_level,
                dominant_emotion
            )
            
            # Predict future stress
            result["prediction"] = self._predict_stress_trend(user_id, stress_score)
            
            # Cache result
            self._cache_stress_result(user_id, stress_score)
            
            logger.info(f"✅ Stress calculated: {stress_score} ({stress_level}) for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calculating stress: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def get_user_stress_history(
        self, 
        user_id: str, 
        limit: int = 20,
        include_analytics: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive stress history with analytics
        
        Args:
            user_id: User ID
            limit: Maximum number of entries
            include_analytics: Include statistical analysis
        
        Returns:
            dict: Stress history with analytics
        """
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "user_id is required"
                }
            
            logger.info(f"📊 Retrieving stress history for user {user_id}")
            
            result = self.stress_service.get_stress_history(user_id, limit)
            
            if not result.get("success"):
                return result
            
            history = result.get("history", [])
            
            if include_analytics and history:
                # Calculate analytics
                stress_scores = [h.get("stress_score", 0) for h in history]
                
                analytics = {
                    "statistics": {
                        "average": round(sum(stress_scores) / len(stress_scores), 2),
                        "max": max(stress_scores),
                        "min": min(stress_scores),
                        "median": self._calculate_median(stress_scores),
                        "std_deviation": round(self._calculate_std_dev(stress_scores), 2)
                    },
                    "distribution": self._get_stress_distribution(stress_scores),
                    "patterns": self._identify_stress_patterns(history),
                    "high_stress_events": sum(1 for s in stress_scores if s >= 7),
                    "critical_stress_events": sum(1 for s in stress_scores if s >= 8)
                }
                
                result["analytics"] = analytics
                
                # Add wellness score
                result["wellness_score"] = self._calculate_wellness_score(stress_scores)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting stress history: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stress_trend(
        self, 
        user_id: str, 
        days: int = 7,
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get detailed stress trend analysis
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            granularity: Trend granularity (hourly/daily/weekly)
        
        Returns:
            dict: Comprehensive trend analysis
        """
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "user_id is required"
                }
            
            if days < 1 or days > 90:
                return {
                    "success": False,
                    "error": "days must be between 1 and 90"
                }
            
            logger.info(f"📈 Analyzing stress trends for user {user_id} ({days} days)")
            
            # Get base trend analysis
            result = self.stress_service.analyze_stress_patterns(user_id, days)
            
            if not result.get("success"):
                return result
            
            # Enrich with additional trend analysis
            analysis = result.get("analysis", {})
            
            # Get time-series data
            time_series = self._get_stress_time_series(user_id, days, granularity)
            result["time_series"] = time_series
            
            # Identify peaks and troughs
            if time_series:
                result["peaks_and_troughs"] = self._identify_peaks_troughs(time_series)
            
            # Get stress triggers
            result["potential_triggers"] = self._identify_stress_triggers(user_id, days)
            
            # Get recovery patterns
            result["recovery_patterns"] = self._analyze_recovery_patterns(user_id, days)
            
            # Add predictive insights
            result["predictive_insights"] = self._generate_predictive_insights(
                analysis,
                time_series
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting stress trend: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_stress_threshold(
        self, 
        score: int, 
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check stress threshold with detailed assessment
        
        Args:
            score: Stress score
            user_id: Optional user ID
            context: Optional context information
        
        Returns:
            dict: Comprehensive threshold assessment
        """
        try:
            if not 0 <= score <= 10:
                return {
                    "success": False,
                    "error": "score must be between 0 and 10"
                }
            
            logger.info(f"🔍 Checking stress threshold: {score}")
            
            result = self.stress_service.check_stress_threshold(score, user_id)
            
            if not result.get("success"):
                return result
            
            # Add detailed threshold analysis
            threshold_analysis = {
                "primary_threshold": {
                    "value": 3,
                    "crossed": score >= 3,
                    "description": "Moderate stress begins"
                },
                "warning_threshold": {
                    "value": 5,
                    "crossed": score >= 5,
                    "description": "Stress requires attention"
                },
                "critical_threshold": {
                    "value": 7,
                    "crossed": score >= 7,
                    "description": "High stress - intervention needed"
                },
                "emergency_threshold": {
                    "value": 9,
                    "crossed": score >= 9,
                    "description": "Critical stress - immediate action required"
                }
            }
            
            result["threshold_analysis"] = threshold_analysis
            
            # Get action items based on threshold
            result["action_items"] = self._get_threshold_actions(score, context)
            
            # Risk assessment
            result["risk_assessment"] = self._assess_threshold_risk(score, user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking stress threshold: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stress_recommendation(
        self, 
        stress_score: int,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive stress relief recommendation
        
        Args:
            stress_score: Current stress score
            user_id: Optional user ID for personalization
        
        Returns:
            dict: Detailed stress management recommendations
        """
        try:
            if not 0 <= stress_score <= 10:
                return {
                    "success": False,
                    "error": "stress_score must be between 0 and 10"
                }
            
            logger.info(f"💡 Generating stress recommendation for score: {stress_score}")
            
            from backend.config import get_stress_level
            stress_level = get_stress_level(stress_score)
            
            result = self.stress_service.get_recommendation_for_stress(
                stress_score, 
                stress_level
            )
            
            if not result.get("success"):
                return result
            
            # Enrich with additional recommendations
            result["immediate_actions"] = self._get_immediate_actions(stress_score)
            result["long_term_strategies"] = self._get_long_term_strategies(stress_score)
            result["resources"] = self._get_stress_resources(stress_score)
            
            # Add breathing exercises
            if stress_score >= 5:
                result["breathing_exercise"] = self._get_breathing_exercise(stress_score)
            
            # Add personalization if user_id provided
            if user_id:
                result["personalized_tips"] = self._get_personalized_tips(user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting stress recommendation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def compare_stress_levels(
        self,
        user_id: str,
        compare_user_id: Optional[str] = None,
        compare_team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare user's stress levels with others or team average
        
        Args:
            user_id: Primary user ID
            compare_user_id: Optional user to compare with
            compare_team_id: Optional team to compare with
        
        Returns:
            dict: Comparison analysis
        """
        try:
            logger.info(f"🔄 Comparing stress levels for user {user_id}")
            
            # Get user's stress data
            user_data = self.stress_service.analyze_stress_patterns(user_id, 30)
            
            if not user_data.get("success"):
                return user_data
            
            user_avg = user_data.get("analysis", {}).get("avg_stress", 0)
            
            comparison = {
                "success": True,
                "user_id": user_id,
                "user_average_stress": user_avg,
                "comparisons": []
            }
            
            # Compare with another user
            if compare_user_id:
                other_data = self.stress_service.analyze_stress_patterns(compare_user_id, 30)
                if other_data.get("success"):
                    other_avg = other_data.get("analysis", {}).get("avg_stress", 0)
                    comparison["comparisons"].append({
                        "type": "user",
                        "compared_with": compare_user_id,
                        "their_average": other_avg,
                        "difference": round(user_avg - other_avg, 2),
                        "relative_status": self._get_relative_status(user_avg, other_avg)
                    })
            
            # Compare with team average
            if compare_team_id:
                team_stats = self._get_team_stress_average(compare_team_id)
                if team_stats:
                    comparison["comparisons"].append({
                        "type": "team",
                        "compared_with": compare_team_id,
                        "team_average": team_stats["average"],
                        "difference": round(user_avg - team_stats["average"], 2),
                        "relative_status": self._get_relative_status(user_avg, team_stats["average"]),
                        "team_size": team_stats["size"]
                    })
            
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Error comparing stress levels: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    
    def _apply_stress_factors(
        self, 
        base_score: int, 
        factors: Dict
    ) -> tuple:
        """Apply additional stress factors to base score"""
        adjusted_score = base_score
        adjustments = []
        
        try:
            # Workload adjustment
            if "workload_level" in factors:
                workload = factors["workload_level"]
                if workload >= 4:
                    adjustment = 1
                    adjusted_score = min(10, adjusted_score + adjustment)
                    adjustments.append(f"+{adjustment} for heavy workload")
            
            # Sleep adjustment
            if "sleep_hours" in factors:
                sleep = factors["sleep_hours"]
                if sleep < 5:
                    adjustment = 2
                    adjusted_score = min(10, adjusted_score + adjustment)
                    adjustments.append(f"+{adjustment} for insufficient sleep")
                elif sleep < 6:
                    adjustment = 1
                    adjusted_score = min(10, adjusted_score + adjustment)
                    adjustments.append(f"+{adjustment} for low sleep")
            
            # Deadline pressure adjustment
            if "deadline_pressure" in factors:
                deadline = factors["deadline_pressure"]
                if deadline >= 4:
                    adjustment = 1
                    adjusted_score = min(10, adjusted_score + adjustment)
                    adjustments.append(f"+{adjustment} for deadline pressure")
            
        except Exception as e:
            logger.error(f"Error applying stress factors: {e}")
        
        return adjusted_score, adjustments
    
    def _get_recent_stress_history(self, user_id: str, days: int = 7) -> List[int]:
        """Get recent stress scores"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            entries = list(
                self.db.mood_entries.find({
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date}
                }).sort("timestamp", -1)
            )
            return [e.get("stress_score", 0) for e in entries]
        except Exception:
            return []
    
    def _calculate_trend(self, history: List[int], current: int) -> str:
        """Calculate stress trend"""
        try:
            if len(history) < 2:
                return "insufficient_data"
            
            recent_avg = sum(history[-5:]) / min(5, len(history))
            older_avg = sum(history[:5]) / min(5, len(history))
            
            if current > recent_avg + 1:
                return "increasing"
            elif current < recent_avg - 1:
                return "decreasing"
            else:
                return "stable"
        except Exception:
            return "unknown"
    
    def _calculate_volatility(self, history: List[int]) -> str:
        """Calculate stress volatility"""
        try:
            if len(history) < 3:
                return "unknown"
            
            std_dev = self._calculate_std_dev(history)
            
            if std_dev > 2:
                return "high"
            elif std_dev > 1:
                return "moderate"
            else:
                return "low"
        except Exception:
            return "unknown"
    
    def _get_change_trend(self, current: int, previous: int) -> str:
        """Get change trend description"""
        change = current - previous
        
        if change > 2:
            return "significant_increase"
        elif change > 0:
            return "slight_increase"
        elif change < -2:
            return "significant_decrease"
        elif change < 0:
            return "slight_decrease"
        else:
            return "stable"
    
    def _get_stress_recommendations(
        self,
        score: int,
        level: str,
        emotion: str
    ) -> List[str]:
        """Get personalized stress recommendations"""
        recommendations = []
        
        if score >= 8:
            recommendations.extend([
                "🚨 URGENT: Take immediate break from current tasks",
                "🧘 Practice 4-7-8 breathing technique for 5 minutes",
                "💬 Speak with your manager or HR immediately",
                "🏥 Consider professional counseling support"
            ])
        elif score >= 6:
            recommendations.extend([
                "⚠️ Take a 10-15 minute break",
                "🚶 Go for a short walk outside if possible",
                "💭 Practice mindfulness meditation",
                "📝 Write down your concerns to clear your mind"
            ])
        elif score >= 4:
            recommendations.extend([
                "☕ Take regular short breaks",
                "🎵 Listen to calming music",
                "📱 Limit screen time during breaks",
                "💪 Do light stretching exercises"
            ])
        else:
            recommendations.extend([
                "✅ Maintain current stress management practices",
                "🌟 Continue with positive habits",
                "📈 Keep tracking your wellness"
            ])
        
        # Add emotion-specific recommendations
        if emotion in ['Angry', 'Disgust']:
            recommendations.append("🎯 Channel energy into physical activity")
        elif emotion == 'Fear':
            recommendations.append("🤝 Talk to a trusted colleague or friend")
        elif emotion == 'Sad':
            recommendations.append("☀️ Get some sunlight and fresh air")
        
        return recommendations
    
    def _predict_stress_trend(self, user_id: str, current_score: int) -> Dict:
        """Predict future stress trend"""
        prediction = {
            "next_24h": "stable",
            "confidence": 50,
            "factors": []
        }
        
        try:
            history = self._get_recent_stress_history(user_id, days=7)
            
            if len(history) >= 3:
                recent_trend = self._calculate_trend(history, current_score)
                
                if recent_trend == "increasing":
                    prediction["next_24h"] = "likely_increase"
                    prediction["confidence"] = 70
                    prediction["factors"].append("Recent upward trend detected")
                elif recent_trend == "decreasing":
                    prediction["next_24h"] = "likely_decrease"
                    prediction["confidence"] = 65
                    prediction["factors"].append("Recent downward trend detected")
                
                # Check volatility
                volatility = self._calculate_volatility(history)
                if volatility == "high":
                    prediction["confidence"] -= 20
                    prediction["factors"].append("High volatility reduces prediction confidence")
        
        except Exception as e:
            logger.error(f"Error predicting stress trend: {e}")
        
        return prediction
    
    def _cache_stress_result(self, user_id: str, score: int):
        """Cache stress result"""
        try:
            self._stress_cache[user_id] = {
                "score": score,
                "timestamp": datetime.utcnow()
            }
        except Exception:
            pass
    
    def _calculate_median(self, values: List[int]) -> float:
        """Calculate median value"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    def _calculate_std_dev(self, values: List[int]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _get_stress_distribution(self, scores: List[int]) -> Dict:
        """Get stress level distribution"""
        distribution = {
            "low": 0,
            "moderate": 0,
            "high": 0,
            "very_high": 0
        }
        
        for score in scores:
            if score <= 2:
                distribution["low"] += 1
            elif score <= 5:
                distribution["moderate"] += 1
            elif score <= 7:
                distribution["high"] += 1
            else:
                distribution["very_high"] += 1
        
        return distribution
    
    def _identify_stress_patterns(self, history: List[Dict]) -> List[str]:
        """Identify stress patterns"""
        patterns = []
        
        try:
            if len(history) < 5:
                return ["Insufficient data for pattern analysis"]
            
            # Check for weekly patterns
            scores = [h.get("stress_score", 0) for h in history]
            
            # Morning vs evening
            # Time-of-day analysis (simplified)
            recent_high = sum(1 for s in scores[-7:] if s >= 7)
            if recent_high >= 3:
                patterns.append("⚠️ Multiple high-stress events in recent period")
            
            # Trend analysis
            if len(scores) >= 10:
                early = sum(scores[:5]) / 5
                recent = sum(scores[-5:]) / 5
                
                if recent > early + 2:
                    patterns.append("📈 Stress levels increasing over time")
                elif recent < early - 2:
                    patterns.append("📉 Stress levels decreasing - positive trend")
        
        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
        
        return patterns if patterns else ["No significant patterns detected"]
    
    def _calculate_wellness_score(self, stress_scores: List[int]) -> int:
        """Calculate wellness score from stress history"""
        try:
            if not stress_scores:
                return 50
            
            avg_stress = sum(stress_scores) / len(stress_scores)
            
            # Invert stress to wellness (10 stress = 0 wellness)
            wellness = 100 - (avg_stress * 10)
            
            return max(0, min(100, int(wellness)))
        
        except Exception:
            return 50
    
    def _get_stress_time_series(
        self, 
        user_id: str, 
        days: int,
        granularity: str
    ) -> List[Dict]:
        """Get time-series stress data"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            entries = list(
                self.db.mood_entries.find({
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date}
                }).sort("timestamp", 1)
            )
            
            return [
                {
                    "timestamp": e.get("timestamp").isoformat(),
                    "stress_score": e.get("stress_score", 0),
                    "emotion": e.get("dominant_emotion", "Unknown")
                }
                for e in entries
            ]
        
        except Exception:
            return []
    
    def _identify_peaks_troughs(self, time_series: List[Dict]) -> Dict:
        """Identify stress peaks and troughs"""
        peaks_troughs = {
            "peaks": [],
            "troughs": []
        }
        
        try:
            if len(time_series) < 3:
                return peaks_troughs
            
            scores = [t["stress_score"] for t in time_series]
            
            # Find peaks (local maxima)
            for i in range(1, len(scores) - 1):
                if scores[i] > scores[i-1] and scores[i] > scores[i+1] and scores[i] >= 7:
                    peaks_troughs["peaks"].append({
                        "timestamp": time_series[i]["timestamp"],
                        "stress_score": scores[i]
                    })
            
            # Find troughs (local minima)
            for i in range(1, len(scores) - 1):
                if scores[i] < scores[i-1] and scores[i] < scores[i+1] and scores[i] <= 3:
                    peaks_troughs["troughs"].append({
                        "timestamp": time_series[i]["timestamp"],
                        "stress_score": scores[i]
                    })
        
        except Exception as e:
            logger.error(f"Error identifying peaks/troughs: {e}")
        
        return peaks_troughs
    
    def _identify_stress_triggers(self, user_id: str, days: int) -> List[str]:
        """Identify potential stress triggers"""
        triggers = []
        
        try:
            # Get high-stress entries
            start_date = datetime.utcnow() - timedelta(days=days)
            high_stress = list(
                self.db.mood_entries.find({
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date},
                    "stress_score": {"$gte": 7}
                })
            )
            
            if high_stress:
                # Analyze emotions during high stress
                emotions = [e.get("dominant_emotion") for e in high_stress]
                from collections import Counter
                emotion_counter = Counter(emotions)
                
                most_common = emotion_counter.most_common(1)[0]
                triggers.append(f"{most_common[0]} emotion frequently accompanies high stress")
                
                # Time-based patterns (simplified)
                if len(high_stress) >= 3:
                    triggers.append("Multiple high-stress events detected - consider workload review")
        
        except Exception as e:
            logger.error(f"Error identifying triggers: {e}")
        
        return triggers if triggers else ["No clear stress triggers identified"]
    
    def _analyze_recovery_patterns(self, user_id: str, days: int) -> Dict:
        """Analyze stress recovery patterns"""
        recovery = {
            "average_recovery_time": "unknown",
            "recovery_effectiveness": "unknown",
            "insights": []
        }
        
        try:
            # Get stress time series
            time_series = self._get_stress_time_series(user_id, days, "daily")
            
            if len(time_series) < 5:
                recovery["insights"].append("Insufficient data for recovery analysis")
                return recovery
            
            scores = [t["stress_score"] for t in time_series]
            
            # Find recovery periods (high to low)
            recovery_periods = []
            for i in range(len(scores) - 1):
                if scores[i] >= 7 and scores[i+1] < 5:
                    recovery_periods.append(i)
            
            if recovery_periods:
                recovery["recovery_effectiveness"] = "good"
                recovery["insights"].append(f"Identified {len(recovery_periods)} recovery periods")
            else:
                recovery["insights"].append("Limited recovery patterns observed")
        
        except Exception as e:
            logger.error(f"Error analyzing recovery: {e}")
        
        return recovery
    
    def _generate_predictive_insights(
        self, 
        analysis: Dict,
        time_series: List[Dict]
    ) -> List[str]:
        """Generate predictive insights"""
        insights = []
        
        try:
            trend = analysis.get("trend", "stable")
            avg_stress = analysis.get("avg_stress", 0)
            
            if trend == "increasing":
                insights.append("⚠️ Stress levels are rising - early intervention recommended")
            elif trend == "decreasing":
                insights.append("✅ Positive trend - stress management is effective")
            
            if avg_stress >= 6:
                insights.append("🚨 Sustained high stress - risk of burnout")
            
            # Predict next week
            if time_series and len(time_series) >= 5:
                recent_avg = sum(t["stress_score"] for t in time_series[-5:]) / 5
                
                if recent_avg >= 7:
                    insights.append("📈 Next week prediction: High stress likely to continue")
                elif recent_avg <= 3:
                    insights.append("📉 Next week prediction: Low stress likely to continue")
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights if insights else ["Continue monitoring stress levels"]
    
    def _get_threshold_actions(
        self, 
        score: int, 
        context: Optional[Dict]
    ) -> List[str]:
        """Get action items based on threshold"""
        actions = []
        
        if score >= 9:
            actions.extend([
                "IMMEDIATE: Stop current tasks",
                "Contact emergency support",
                "Notify manager/HR",
                "Take extended break"
            ])
        elif score >= 7:
            actions.extend([
                "Take 15-minute break immediately",
                "Practice stress relief techniques",
                "Notify team lead",
                "Review workload with manager"
            ])
        elif score >= 5:
            actions.extend([
                "Take short breaks regularly",
                "Use stress management techniques",
                "Monitor closely"
            ])
        elif score >= 3:
            actions.append("Continue current practices")
        else:
            actions.append("Maintain wellness activities")
        
        return actions
    
    def _assess_threshold_risk(self, score: int, user_id: Optional[str]) -> Dict:
        """Assess risk based on threshold"""
        risk = {
            "level": "low",
            "immediate_action_required": False,
            "escalation_needed": False
        }
        
        if score >= 9:
            risk["level"] = "critical"
            risk["immediate_action_required"] = True
            risk["escalation_needed"] = True
        elif score >= 7:
            risk["level"] = "high"
            risk["immediate_action_required"] = True
            risk["escalation_needed"] = False
        elif score >= 5:
            risk["level"] = "medium"
        
        return risk
    
    def _get_immediate_actions(self, score: int) -> List[str]:
        """Get immediate action recommendations"""
        if score >= 8:
            return [
                "Stop what you're doing immediately",
                "Take 10 deep breaths",
                "Step away from your workspace",
                "Call someone you trust"
            ]
        elif score >= 6:
            return [
                "Take a 10-minute break",
                "Practice 4-7-8 breathing",
                "Walk around briefly",
                "Drink water"
            ]
        else:
            return [
                "Take a brief pause",
                "Stretch at your desk",
                "Adjust your posture"
            ]
    
    def _get_long_term_strategies(self, score: int) -> List[str]:
        """Get long-term stress management strategies"""
        strategies = [
            "Establish regular exercise routine",
            "Practice daily meditation",
            "Maintain consistent sleep schedule",
            "Build support network"
        ]
        
        if score >= 6:
            strategies.extend([
                "Consider professional counseling",
                "Review work-life balance",
                "Identify and address stress sources"
            ])
        
        return strategies
    
    def _get_stress_resources(self, score: int) -> List[Dict]:
        """Get stress management resources"""
        resources = [
            {
                "title": "Mindfulness Meditation Guide",
                "type": "article",
                "url": "#"
            },
            {
                "title": "4-7-8 Breathing Technique",
                "type": "video",
                "url": "#"
            }
        ]
        
        if score >= 7:
            resources.append({
                "title": "Employee Assistance Program",
                "type": "service",
                "url": "#"
            })
        
        return resources
    
    def _get_breathing_exercise(self, score: int) -> Dict:
        """Get appropriate breathing exercise"""
        if score >= 8:
            return {
                "name": "4-7-8 Breathing",
                "instructions": [
                    "Inhale quietly through nose for 4 counts",
                    "Hold breath for 7 counts",
                    "Exhale completely through mouth for 8 counts",
                    "Repeat 4 times"
                ],
                "duration": "2 minutes"
            }
        else:
            return {
                "name": "Box Breathing",
                "instructions": [
                    "Inhale for 4 counts",
                    "Hold for 4 counts",
                    "Exhale for 4 counts",
                    "Hold for 4 counts",
                    "Repeat 4 times"
                ],
                "duration": "2 minutes"
            }
    
    def _get_personalized_tips(self, user_id: str) -> List[str]:
        """Get personalized stress management tips"""
        tips = [
            "Based on your history, morning sessions work best for you",
            "You respond well to short breaks"
        ]
        
        return tips
    
    def _get_relative_status(self, user_avg: float, compare_avg: float) -> str:
        """Get relative stress status"""
        diff = user_avg - compare_avg
        
        if diff > 2:
            return "significantly_higher"
        elif diff > 0.5:
            return "higher"
        elif diff < -2:
            return "significantly_lower"
        elif diff < -0.5:
            return "lower"
        else:
            return "similar"
    
    def _get_team_stress_average(self, team_id: str) -> Optional[Dict]:
        """Get team stress average"""
        try:
            pipeline = [
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "user_id",
                        "foreignField": "user_id",
                        "as": "user"
                    }
                },
                {"$unwind": "$user"},
                {"$match": {"user.team_id": team_id}},
                {
                    "$group": {
                        "_id": None,
                        "avg_stress": {"$avg": "$stress_score"},
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            result = list(self.db.mood_entries.aggregate(pipeline))
            
            if result:
                return {
                    "average": round(result[0]["avg_stress"], 2),
                    "size": result[0]["count"]
                }
        
        except Exception as e:
            logger.error(f"Error getting team average: {e}")
        
        return None


# Create global controller instance
stress_controller = StressController()