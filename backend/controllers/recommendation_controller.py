"""
Enhanced Recommendation Controller for Amdox
Production-grade task recommendations with context awareness and intelligent matching
"""
import sys
import os
from datetime import datetime
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

from backend.services.recommendation_service import recommendation_service
from backend.database.db import db_manager


class RecommendationController:
    """
    Enhanced Controller for recommendation endpoints with advanced context processing
    """
    
    def __init__(self):
        self.recommendation_service = recommendation_service
        self.db = db_manager.get_database()
        self._recommendation_history = {}  # Track user recommendation history
        logger.info("✅ Recommendation Controller initialized")
    
    def recommend_task(
        self, 
        dominant_emotion: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get intelligent task recommendation based on emotion and context
        
        Args:
            dominant_emotion: The detected dominant emotion
            context: Optional context (stress_score, workload_level, etc.)
            user_id: Optional user ID for personalization
        
        Returns:
            dict: Comprehensive task recommendation
        """
        try:
            # Validate emotion
            valid_emotions = ['Happy', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust', 'Neutral']
            if dominant_emotion not in valid_emotions:
                return {
                    "success": False,
                    "error": f"Invalid emotion. Must be one of: {', '.join(valid_emotions)}"
                }
            
            logger.info(f"🎯 Generating recommendation for emotion: {dominant_emotion}")
            
            # Get base recommendation from service
            result = self.recommendation_service.recommend_task(
                dominant_emotion=dominant_emotion,
                context=context
            )
            
            if not result.get("success"):
                return result
            
            # Enrich with additional insights
            if context:
                result["contextual_insights"] = self._generate_contextual_insights(context)
            
            # Add personalization if user_id provided
            if user_id:
                result["personalization"] = self._add_personalization(
                    user_id, 
                    dominant_emotion,
                    result.get("recommendation", {})
                )
            
            # Add follow-up actions
            result["follow_up_actions"] = self._get_follow_up_actions(
                dominant_emotion,
                context.get("stress_score", 0) if context else 0
            )
            
            # Track recommendation
            if user_id:
                self._track_recommendation(user_id, dominant_emotion, result)
            
            logger.info(f"✅ Recommendation generated successfully for {dominant_emotion}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def get_multiple_recommendations(
        self, 
        dominant_emotion: str, 
        count: int = 3,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get multiple task suggestions with priority ranking
        
        Args:
            dominant_emotion: The detected dominant emotion
            count: Number of suggestions to return (1-10)
            user_id: Optional user ID for personalization
        
        Returns:
            dict: Multiple recommendations with priorities
        """
        try:
            # Validate inputs
            if count < 1 or count > 10:
                return {
                    "success": False,
                    "error": "count must be between 1 and 10"
                }
            
            logger.info(f"🎯 Generating {count} recommendations for {dominant_emotion}")
            
            # Get base recommendations
            result = self.recommendation_service.get_multiple_recommendations(
                dominant_emotion=dominant_emotion,
                count=count
            )
            
            if not result.get("success"):
                return result
            
            # Enrich each suggestion
            suggestions = result.get("suggestions", [])
            enriched_suggestions = []
            
            for idx, suggestion in enumerate(suggestions):
                enriched = {
                    **suggestion,
                    "rank": idx + 1,
                    "estimated_impact": self._calculate_impact_score(
                        suggestion.get("task", ""),
                        dominant_emotion
                    ),
                    "difficulty": self._estimate_difficulty(suggestion.get("task", "")),
                    "best_time": self._suggest_best_time(suggestion.get("category", ""))
                }
                enriched_suggestions.append(enriched)
            
            result["suggestions"] = enriched_suggestions
            
            # Add recommendation strategy explanation
            result["strategy"] = self._explain_recommendation_strategy(
                dominant_emotion,
                len(suggestions)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting multiple recommendations: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_emotion_based_tasks(self, include_examples: bool = True) -> Dict[str, Any]:
        """
        Get all available tasks organized by emotion with examples
        
        Args:
            include_examples: Whether to include task examples
        
        Returns:
            dict: Emotion-task mapping with metadata
        """
        try:
            logger.info("📚 Retrieving emotion-based task catalog")
            
            result = self.recommendation_service.get_emotion_based_tasks()
            
            if not result.get("success"):
                return result
            
            # Enrich with additional metadata
            emotion_task_mapping = result.get("emotion_task_mapping", {})
            
            for emotion, config in emotion_task_mapping.items():
                # Add task count
                config["task_count"] = len(config.get("tasks", []))
                
                # Add effectiveness rating
                config["effectiveness_rating"] = self._get_effectiveness_rating(emotion)
                
                # Add best use cases
                config["best_for"] = self._get_best_use_cases(emotion)
                
                # Add examples if requested
                if include_examples:
                    config["examples"] = self._get_task_examples(emotion)
            
            result["emotion_task_mapping"] = emotion_task_mapping
            result["total_emotions"] = len(emotion_task_mapping)
            result["total_tasks"] = sum(
                len(config.get("tasks", [])) 
                for config in emotion_task_mapping.values()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting emotion-based tasks: {e}", exc_info=True)
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
        sleep_hours: Optional[float] = None,
        time_of_day: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive recommendation with full context analysis
        
        Args:
            dominant_emotion: The detected dominant emotion
            stress_score: Current stress score (0-10)
            workload_level: Workload level (1-5)
            deadline_pressure: Deadline pressure (1-5)
            sleep_hours: Hours of sleep last night
            time_of_day: Current time of day (morning/afternoon/evening)
            user_id: Optional user ID
        
        Returns:
            dict: Context-aware recommendation with detailed analysis
        """
        try:
            logger.info(f"🎯 Generating context-aware recommendation for {dominant_emotion}")
            
            # Build context dictionary
            context = {}
            if stress_score is not None:
                if not 0 <= stress_score <= 10:
                    return {
                        "success": False,
                        "error": "stress_score must be between 0 and 10"
                    }
                context["stress_score"] = stress_score
            
            if workload_level is not None:
                if not 1 <= workload_level <= 5:
                    return {
                        "success": False,
                        "error": "workload_level must be between 1 and 5"
                    }
                context["workload_level"] = workload_level
            
            if deadline_pressure is not None:
                if not 1 <= deadline_pressure <= 5:
                    return {
                        "success": False,
                        "error": "deadline_pressure must be between 1 and 5"
                    }
                context["deadline_pressure"] = deadline_pressure
            
            if sleep_hours is not None:
                if not 0 <= sleep_hours <= 24:
                    return {
                        "success": False,
                        "error": "sleep_hours must be between 0 and 24"
                    }
                context["sleep_hours"] = sleep_hours
            
            if time_of_day:
                context["time_of_day"] = time_of_day
            
            # Get base recommendation
            result = self.recommendation_service.recommend_task(
                dominant_emotion=dominant_emotion,
                context=context
            )
            
            if not result.get("success"):
                return result
            
            # Add comprehensive contextual analysis
            result["context_analysis"] = self._analyze_context(context)
            
            # Add risk assessment
            result["risk_assessment"] = self._assess_risk(
                dominant_emotion,
                stress_score or 0,
                workload_level or 3
            )
            
            # Add optimal timing
            result["optimal_timing"] = self._determine_optimal_timing(
                context,
                dominant_emotion
            )
            
            # Add energy level assessment
            result["energy_assessment"] = self._assess_energy_level(
                sleep_hours or 7,
                time_of_day or "unknown"
            )
            
            # Add alternative recommendations
            result["alternatives"] = self._get_alternative_recommendations(
                dominant_emotion,
                context,
                count=2
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting contextual recommendation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recommendation_feedback(
        self,
        user_id: str,
        recommendation_id: str,
        helpful: bool,
        followed: bool,
        feedback_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback on recommendations
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            helpful: Was the recommendation helpful
            followed: Did the user follow the recommendation
            feedback_text: Optional feedback text
        
        Returns:
            dict: Feedback confirmation
        """
        try:
            logger.info(f"📝 Recording feedback for recommendation {recommendation_id}")
            
            feedback = {
                "user_id": user_id,
                "recommendation_id": recommendation_id,
                "helpful": helpful,
                "followed": followed,
                "feedback_text": feedback_text,
                "timestamp": datetime.utcnow()
            }
            
            # Save to database
            self.db.recommendation_feedback.insert_one(feedback)
            
            return {
                "success": True,
                "message": "Feedback recorded successfully",
                "thank_you": "Thank you for helping us improve our recommendations!"
            }
            
        except Exception as e:
            logger.error(f"❌ Error recording feedback: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    
    def _generate_contextual_insights(self, context: Dict) -> Dict[str, Any]:
        """Generate insights based on context"""
        insights = {
            "factors_considered": [],
            "warnings": [],
            "suggestions": [],
            "priority_adjustments": []
        }
        
        try:
            if context.get("stress_score", 0) >= 7:
                insights["warnings"].append("⚠️ High stress detected - recommendations prioritize stress relief")
                insights["factors_considered"].append("stress_score")
                insights["priority_adjustments"].append("Increased priority for calming activities")
            
            if context.get("workload_level", 0) >= 4:
                insights["warnings"].append("📊 Heavy workload detected - consider delegating or rescheduling")
                insights["factors_considered"].append("workload_level")
                insights["suggestions"].append("Break large tasks into smaller chunks")
            
            if context.get("deadline_pressure", 0) >= 4:
                insights["warnings"].append("⏰ High deadline pressure - focus on critical tasks only")
                insights["factors_considered"].append("deadline_pressure")
                insights["priority_adjustments"].append("Shifted to time-sensitive tasks")
            
            if context.get("sleep_hours", 8) < 6:
                insights["suggestions"].append("😴 Low sleep detected - consider shorter, focused work sessions")
                insights["factors_considered"].append("sleep_hours")
                insights["warnings"].append("⚡ Energy levels may be lower than normal")
            
            if not insights["warnings"]:
                insights["suggestions"].append("✅ Current context appears favorable for focused work")
            
        except Exception as e:
            logger.error(f"Error generating contextual insights: {e}")
        
        return insights
    
    def _add_personalization(
        self, 
        user_id: str, 
        emotion: str,
        recommendation: Dict
    ) -> Dict[str, Any]:
        """Add personalization based on user history"""
        personalization = {
            "based_on_history": False,
            "user_preferences": [],
            "past_effectiveness": None
        }
        
        try:
            # Get user's past recommendations
            past_recs = list(
                self.db.recommendation_feedback.find({
                    "user_id": user_id
                }).limit(10)
            )
            
            if past_recs:
                personalization["based_on_history"] = True
                
                # Calculate effectiveness
                helpful_count = sum(1 for r in past_recs if r.get("helpful"))
                personalization["past_effectiveness"] = round(
                    (helpful_count / len(past_recs)) * 100, 1
                )
            
        except Exception as e:
            logger.error(f"Error adding personalization: {e}")
        
        return personalization
    
    def _get_follow_up_actions(
        self, 
        emotion: str, 
        stress_score: int
    ) -> List[str]:
        """Get recommended follow-up actions"""
        actions = []
        
        if stress_score >= 7:
            actions.extend([
                "Schedule a follow-up check-in in 30 minutes",
                "Notify your team lead about high stress",
                "Review today's priorities and adjust if needed"
            ])
        elif emotion in ['Sad', 'Angry', 'Fear']:
            actions.extend([
                "Set a reminder to reassess in 1 hour",
                "Consider reaching out to a colleague for support"
            ])
        else:
            actions.append("Continue with recommended task and track progress")
        
        return actions
    
    def _calculate_impact_score(self, task: str, emotion: str) -> str:
        """Calculate expected impact of task"""
        # Simple scoring based on emotion-task alignment
        impact_map = {
            'Happy': 'High',
            'Neutral': 'Medium',
            'Sad': 'High',
            'Angry': 'High',
            'Fear': 'Medium',
            'Surprise': 'Medium',
            'Disgust': 'Medium'
        }
        return impact_map.get(emotion, 'Medium')
    
    def _estimate_difficulty(self, task: str) -> str:
        """Estimate task difficulty"""
        # Keywords for difficulty estimation
        easy_keywords = ['break', 'walk', 'breathing', 'listen']
        hard_keywords = ['complex', 'analyze', 'strategic', 'planning']
        
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in easy_keywords):
            return 'Easy'
        elif any(keyword in task_lower for keyword in hard_keywords):
            return 'Hard'
        else:
            return 'Medium'
    
    def _suggest_best_time(self, category: str) -> str:
        """Suggest best time for task category"""
        time_map = {
            'Creative': 'Morning (peak creativity)',
            'Wellness': 'Anytime (especially when stressed)',
            'Focus': 'Morning or early afternoon',
            'Calming': 'Whenever needed',
            'Productivity': 'Mid-morning',
            'Exploration': 'Afternoon'
        }
        return time_map.get(category, 'Anytime')
    
    def _explain_recommendation_strategy(
        self, 
        emotion: str, 
        count: int
    ) -> str:
        """Explain the recommendation strategy"""
        strategies = {
            'Happy': f"Leveraging your positive mood with {count} creative and collaborative tasks",
            'Sad': f"Providing {count} wellness-focused activities to improve mood",
            'Angry': f"Offering {count} calming activities to reduce tension",
            'Fear': f"Suggesting {count} structured tasks to build confidence",
            'Neutral': f"Presenting {count} balanced tasks for steady productivity",
            'Surprise': f"Channeling curiosity with {count} exploratory tasks",
            'Disgust': f"Recommending {count} organizational tasks to restore order"
        }
        return strategies.get(emotion, f"Providing {count} appropriate tasks")
    
    def _get_effectiveness_rating(self, emotion: str) -> float:
        """Get effectiveness rating for emotion-based recommendations"""
        # Based on typical user feedback (simulated)
        ratings = {
            'Happy': 4.5,
            'Neutral': 4.2,
            'Sad': 4.0,
            'Angry': 4.3,
            'Fear': 3.9,
            'Surprise': 4.1,
            'Disgust': 3.8
        }
        return ratings.get(emotion, 4.0)
    
    def _get_best_use_cases(self, emotion: str) -> List[str]:
        """Get best use cases for emotion"""
        use_cases = {
            'Happy': ['Creative projects', 'Team collaboration', 'Innovation sessions'],
            'Neutral': ['Routine tasks', 'Documentation', 'Email management'],
            'Sad': ['Self-care', 'Low-pressure tasks', 'Supportive conversations'],
            'Angry': ['Physical activity', 'Stress relief', 'Meditation'],
            'Fear': ['Structured tasks', 'Guided activities', 'Skill building'],
            'Surprise': ['Learning', 'Exploration', 'New challenges'],
            'Disgust': ['Organization', 'Cleanup', 'Process improvement']
        }
        return use_cases.get(emotion, ['General tasks'])
    
    def _get_task_examples(self, emotion: str) -> List[str]:
        """Get specific task examples"""
        examples = {
            'Happy': ['Brainstorm new product ideas', 'Lead a team standup', 'Design user interface mockups'],
            'Neutral': ['Process emails', 'Update documentation', 'Review code'],
            'Sad': ['Take a nature walk', 'Listen to uplifting music', 'Practice gratitude journaling'],
            'Angry': ['Do 10 minutes of yoga', 'Practice box breathing', 'Go for a brisk walk'],
            'Fear': ['Complete a tutorial', 'Review checklist', 'Pair program with colleague'],
            'Surprise': ['Research new technology', 'Attend a webinar', 'Experiment with new tools'],
            'Disgust': ['Organize desktop', 'Clean up codebase', 'Optimize workflows']
        }
        return examples.get(emotion, ['General work tasks'])
    
    def _analyze_context(self, context: Dict) -> Dict[str, Any]:
        """Analyze full context"""
        analysis = {
            "overall_state": "unknown",
            "key_factors": [],
            "risk_level": "low",
            "recommendations_adjusted": False
        }
        
        try:
            stress = context.get("stress_score", 0)
            workload = context.get("workload_level", 3)
            deadline = context.get("deadline_pressure", 3)
            
            # Determine overall state
            if stress >= 7 or workload >= 4 or deadline >= 4:
                analysis["overall_state"] = "high_pressure"
                analysis["risk_level"] = "high"
            elif stress >= 5 or workload >= 3:
                analysis["overall_state"] = "moderate_pressure"
                analysis["risk_level"] = "medium"
            else:
                analysis["overall_state"] = "comfortable"
                analysis["risk_level"] = "low"
            
            # Identify key factors
            if stress >= 6:
                analysis["key_factors"].append("Elevated stress levels")
            if workload >= 4:
                analysis["key_factors"].append("Heavy workload")
            if deadline >= 4:
                analysis["key_factors"].append("Tight deadlines")
            
            analysis["recommendations_adjusted"] = len(analysis["key_factors"]) > 0
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
        
        return analysis
    
    def _assess_risk(
        self, 
        emotion: str, 
        stress: int, 
        workload: int
    ) -> Dict[str, Any]:
        """Assess burnout/wellness risk"""
        risk = {
            "level": "low",
            "score": 0,
            "factors": [],
            "mitigation": []
        }
        
        try:
            score = 0
            
            # Emotion risk
            if emotion in ['Angry', 'Sad', 'Fear']:
                score += 30
                risk["factors"].append("Negative emotional state")
            
            # Stress risk
            if stress >= 7:
                score += 40
                risk["factors"].append("High stress levels")
            elif stress >= 5:
                score += 20
                risk["factors"].append("Moderate stress")
            
            # Workload risk
            if workload >= 4:
                score += 30
                risk["factors"].append("Heavy workload")
            
            risk["score"] = min(100, score)
            
            # Determine level
            if score >= 70:
                risk["level"] = "high"
                risk["mitigation"] = [
                    "Immediate intervention recommended",
                    "Contact HR or manager",
                    "Take mandatory break"
                ]
            elif score >= 40:
                risk["level"] = "medium"
                risk["mitigation"] = [
                    "Monitor closely",
                    "Implement stress reduction techniques",
                    "Review workload distribution"
                ]
            else:
                risk["level"] = "low"
                risk["mitigation"] = ["Continue current practices"]
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
        
        return risk
    
    def _determine_optimal_timing(
        self, 
        context: Dict, 
        emotion: str
    ) -> Dict[str, Any]:
        """Determine optimal timing for tasks"""
        timing = {
            "best_start_time": "now",
            "expected_duration": "30-45 minutes",
            "flexibility": "medium",
            "reasoning": []
        }
        
        try:
            time_of_day = context.get("time_of_day", "unknown")
            stress = context.get("stress_score", 0)
            
            if stress >= 7:
                timing["best_start_time"] = "immediately"
                timing["expected_duration"] = "10-15 minutes"
                timing["flexibility"] = "none"
                timing["reasoning"].append("High stress requires immediate action")
            elif time_of_day == "morning":
                timing["reasoning"].append("Morning is optimal for focused work")
            elif time_of_day == "evening":
                timing["best_start_time"] = "within 30 minutes"
                timing["reasoning"].append("Evening energy levels may be lower")
            
        except Exception as e:
            logger.error(f"Error determining optimal timing: {e}")
        
        return timing
    
    def _assess_energy_level(
        self, 
        sleep_hours: float, 
        time_of_day: str
    ) -> Dict[str, Any]:
        """Assess user's energy level"""
        assessment = {
            "level": "medium",
            "score": 50,
            "factors": [],
            "recommendations": []
        }
        
        try:
            score = 50
            
            # Sleep impact
            if sleep_hours >= 7:
                score += 30
                assessment["factors"].append("Good sleep (7+ hours)")
            elif sleep_hours >= 5:
                score += 10
                assessment["factors"].append("Adequate sleep (5-7 hours)")
            else:
                score -= 30
                assessment["factors"].append("Insufficient sleep (<5 hours)")
                assessment["recommendations"].append("Consider caffeine or short break")
            
            # Time of day impact
            if time_of_day == "morning":
                score += 20
                assessment["factors"].append("Morning energy boost")
            elif time_of_day == "evening":
                score -= 20
                assessment["factors"].append("Evening energy dip")
            
            assessment["score"] = max(0, min(100, score))
            
            # Determine level
            if score >= 70:
                assessment["level"] = "high"
            elif score >= 40:
                assessment["level"] = "medium"
            else:
                assessment["level"] = "low"
                assessment["recommendations"].append("Take short breaks frequently")
            
        except Exception as e:
            logger.error(f"Error assessing energy level: {e}")
        
        return assessment
    
    def _get_alternative_recommendations(
        self,
        emotion: str,
        context: Dict,
        count: int = 2
    ) -> List[Dict]:
        """Get alternative recommendations"""
        alternatives = []
        
        try:
            # Get multiple recommendations
            result = self.recommendation_service.get_multiple_recommendations(
                dominant_emotion=emotion,
                count=count + 1  # Get one extra
            )
            
            if result.get("success"):
                suggestions = result.get("suggestions", [])
                # Skip first (main recommendation) and return rest
                alternatives = [
                    {
                        "task": s.get("task"),
                        "category": s.get("category"),
                        "priority": s.get("priority"),
                        "reason": f"Alternative {emotion.lower()} task"
                    }
                    for s in suggestions[1:count+1]
                ]
        
        except Exception as e:
            logger.error(f"Error getting alternatives: {e}")
        
        return alternatives
    
    def _track_recommendation(
        self, 
        user_id: str, 
        emotion: str, 
        recommendation: Dict
    ):
        """Track recommendation in history"""
        try:
            if user_id not in self._recommendation_history:
                self._recommendation_history[user_id] = []
            
            self._recommendation_history[user_id].append({
                "timestamp": datetime.utcnow(),
                "emotion": emotion,
                "recommendation": recommendation.get("recommendation", {}).get("task")
            })
            
            # Keep only last 10 recommendations per user
            self._recommendation_history[user_id] = \
                self._recommendation_history[user_id][-10:]
            
        except Exception as e:
            logger.error(f"Error tracking recommendation: {e}")


# Create global controller instance
recommendation_controller = RecommendationController()