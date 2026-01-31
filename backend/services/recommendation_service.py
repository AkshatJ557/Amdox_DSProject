"""
Enhanced Recommendation Service for Amdox - ALIGNED WITH NOTEBOOK
Context-aware task recommendations using Green/Yellow/Orange/Red zones
"""
import sys
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import will work when file is in correct location
try:
    from backend.config import (
        TASK_RECOMMENDATIONS,
        EMOTION_TO_ZONE,
        TASK_ZONES,
        get_tasks_for_emotion,
        get_task_zone_for_emotion
    )
except ImportError:
    # Fallback for standalone testing
    logger.warning("⚠️ Using fallback config")
    TASK_RECOMMENDATIONS = {}
    EMOTION_TO_ZONE = {}
    TASK_ZONES = {}
    
    def get_tasks_for_emotion(emotion):
        return {}
    
    def get_task_zone_for_emotion(emotion):
        return 'YELLOW'


class RecommendationService:
    """
    Enhanced Task Recommendation Service with notebook-aligned zones
    """
    
    def __init__(self):
        self.recommendations = TASK_RECOMMENDATIONS
        self.emotion_to_zone = EMOTION_TO_ZONE
        self.task_zones = TASK_ZONES
        self._recommendation_cache = {}
        logger.info("💡 Recommendation Service initialized")
    
    def recommend_task(
        self,
        dominant_emotion: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get task recommendation based on emotion and context
        
        Args:
            dominant_emotion: Detected emotion
            context: Optional context (stress_score, workload, etc.)
        
        Returns:
            dict: Task recommendation with zone info
        """
        try:
            # Get tasks for emotion
            emotion_tasks = get_tasks_for_emotion(dominant_emotion)
            
            if not emotion_tasks:
                logger.warning(f"⚠️ No tasks found for emotion: {dominant_emotion}")
                return {
                    "success": False,
                    "error": f"No recommendations available for emotion: {dominant_emotion}"
                }
            
            # Get zone info
            zone = emotion_tasks.get('zone', 'YELLOW')
            zone_name = emotion_tasks.get('zone_name', 'Yellow_Routine_Task')
            tasks_list = emotion_tasks.get('tasks', [])
            
            if not tasks_list:
                return {
                    "success": False,
                    "error": "No tasks available in zone"
                }
            
            # Select best task based on context
            selected_task = self._select_best_task(tasks_list, context)
            
            # Calculate confidence based on context completeness
            confidence = self._calculate_confidence(context)
            
            # Get zone details
            zone_info = self.task_zones.get(zone, {})
            
            result = {
                "success": True,
                "dominant_emotion": dominant_emotion,
                "recommendation": selected_task,
                "zone": zone,
                "zone_name": zone_name,
                "zone_info": {
                    "description": zone_info.get('description', ''),
                    "energy_level": zone_info.get('energy_level', ''),
                    "color": zone_info.get('color', '#FFC107')
                },
                "confidence": confidence,
                "context_used": context is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add contextual insights if context provided
            if context:
                result["contextual_insights"] = self._generate_insights(
                    context,
                    selected_task,
                    zone
                )
            
            logger.debug(f"💡 Recommendation: {selected_task['task']} ({zone})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _select_best_task(
        self,
        tasks: List[Dict],
        context: Optional[Dict]
    ) -> Dict:
        """
        Select the most appropriate task based on context
        
        Args:
            tasks: List of available tasks
            context: User context
        
        Returns:
            dict: Selected task
        """
        if not context:
            # No context - return highest priority task
            return tasks[0]
        
        # Score each task based on context
        scored_tasks = []
        
        for task in tasks:
            score = 0
            
            # Priority scoring
            priority_scores = {
                'Critical': 100,
                'High': 75,
                'Medium': 50,
                'Low': 25
            }
            score += priority_scores.get(task.get('priority', 'Medium'), 50)
            
            # Stress-based scoring
            stress_score = context.get('stress_score', 5)
            if stress_score >= 7:
                # High stress - prefer recovery/break tasks
                if task.get('category') in ['Break', 'Stress recovery']:
                    score += 50
            elif stress_score <= 3:
                # Low stress - prefer creative/challenging tasks
                if task.get('category') in ['Creative', 'Innovation']:
                    score += 50
            
            # Workload-based scoring
            workload = context.get('workload_level', 5)
            if workload >= 7:
                # High workload - prefer light tasks
                if task.get('category') in ['Light tasks', 'Break']:
                    score += 30
            
            # Time availability
            if 'time_available' in context:
                task_duration = self._parse_duration(task.get('duration', '30 minutes'))
                if task_duration <= context['time_available']:
                    score += 20
            
            scored_tasks.append((score, task))
        
        # Sort by score and return best
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return scored_tasks[0][1]
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to minutes (approximate)"""
        try:
            # Extract first number
            import re
            numbers = re.findall(r'\d+', duration_str)
            if numbers:
                return int(numbers[0])
        except Exception:
            pass
        return 30  # Default
    
    def _calculate_confidence(self, context: Optional[Dict]) -> float:
        """
        Calculate recommendation confidence based on context
        
        Args:
            context: User context
        
        Returns:
            float: Confidence score (0-1)
        """
        if not context:
            return 0.6  # Base confidence with emotion only
        
        confidence = 0.6
        
        # Add confidence for each context factor
        factors = [
            'stress_score',
            'workload_level',
            'deadline_pressure',
            'sleep_hours',
            'working_hours'
        ]
        
        available_factors = sum(1 for f in factors if f in context)
        confidence += (available_factors / len(factors)) * 0.4
        
        return round(min(1.0, confidence), 2)
    
    def _generate_insights(
        self,
        context: Dict,
        task: Dict,
        zone: str
    ) -> List[str]:
        """Generate contextual insights for the recommendation"""
        insights = []
        
        try:
            stress = context.get('stress_score', 0)
            workload = context.get('workload_level', 0)
            
            # Stress-based insights
            if stress >= 7:
                insights.append(f"⚠️ High stress detected - {zone} zone task recommended for recovery")
            elif stress <= 3:
                insights.append(f"✅ Low stress - good opportunity for {zone} zone productivity")
            
            # Workload insights
            if workload >= 7:
                insights.append("📊 Heavy workload - task selected to prevent overwhelm")
            
            # Task-specific insights
            if task.get('category') == 'Break':
                insights.append("💤 Break recommended to restore energy and focus")
            elif task.get('category') == 'Creative':
                insights.append("🎨 Your current state is optimal for creative work")
            
            # Time insights
            if 'working_hours' in context and context['working_hours'] >= 10:
                insights.append("⏰ Extended work hours - consider shorter tasks")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    def get_multiple_recommendations(
        self,
        dominant_emotion: str,
        count: int = 3,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get multiple task recommendations
        
        Args:
            dominant_emotion: Detected emotion
            count: Number of recommendations (1-10)
            context: Optional context
        
        Returns:
            dict: Multiple recommendations
        """
        try:
            if count < 1 or count > 10:
                return {
                    "success": False,
                    "error": "count must be between 1 and 10"
                }
            
            # Get tasks for emotion
            emotion_tasks = get_tasks_for_emotion(dominant_emotion)
            
            if not emotion_tasks:
                return {
                    "success": False,
                    "error": f"No recommendations for emotion: {dominant_emotion}"
                }
            
            tasks_list = emotion_tasks.get('tasks', [])
            zone = emotion_tasks.get('zone', 'YELLOW')
            zone_name = emotion_tasks.get('zone_name', '')
            
            # Limit to available tasks
            count = min(count, len(tasks_list))
            
            # Score and rank tasks
            if context:
                scored_tasks = []
                for task in tasks_list[:count * 2]:  # Get more than needed for filtering
                    score = self._score_task(task, context)
                    scored_tasks.append((score, task))
                
                scored_tasks.sort(key=lambda x: x[0], reverse=True)
                selected_tasks = [task for _, task in scored_tasks[:count]]
            else:
                selected_tasks = tasks_list[:count]
            
            # Add ranking
            suggestions = []
            for idx, task in enumerate(selected_tasks, 1):
                task_copy = task.copy()
                task_copy['rank'] = idx
                task_copy['confidence'] = self._calculate_confidence(context)
                suggestions.append(task_copy)
            
            return {
                "success": True,
                "dominant_emotion": dominant_emotion,
                "zone": zone,
                "zone_name": zone_name,
                "suggestions": suggestions,
                "count": len(suggestions)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting multiple recommendations: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _score_task(self, task: Dict, context: Dict) -> float:
        """Score a task based on context fit"""
        score = 0.0
        
        # Priority weight
        priority_map = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        score += priority_map.get(task.get('priority', 'Medium'), 2) * 10
        
        # Context alignment
        stress = context.get('stress_score', 5)
        
        if stress >= 7:
            # Prefer recovery tasks
            if task.get('category') in ['Break', 'Stress recovery', 'Peer support']:
                score += 30
        elif stress <= 3:
            # Prefer productive tasks
            if task.get('category') in ['Creative', 'Innovation', 'Teamwork']:
                score += 30
        
        return score
    
    def get_emotion_based_tasks(self) -> Dict[str, Any]:
        """
        Get all available tasks organized by emotion
        
        Returns:
            dict: Complete task catalog
        """
        try:
            emotion_task_mapping = {}
            
            for emotion, tasks_data in self.recommendations.items():
                zone = tasks_data.get('zone', 'YELLOW')
                zone_info = self.task_zones.get(zone, {})
                
                emotion_task_mapping[emotion] = {
                    "zone": zone,
                    "zone_name": tasks_data.get('zone_name', ''),
                    "zone_description": zone_info.get('description', ''),
                    "energy_level": zone_info.get('energy_level', ''),
                    "task_count": len(tasks_data.get('tasks', [])),
                    "tasks": tasks_data.get('tasks', [])
                }
            
            return {
                "success": True,
                "emotion_task_mapping": emotion_task_mapping,
                "total_emotions": len(emotion_task_mapping),
                "zones": list(self.task_zones.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting emotion-based tasks: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_zone_recommendations(
        self,
        zone: str,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Get recommendations for a specific task zone
        
        Args:
            zone: Task zone (GREEN/YELLOW/ORANGE/RED)
            count: Number of recommendations
        
        Returns:
            dict: Zone-specific recommendations
        """
        try:
            zone = zone.upper()
            
            if zone not in self.task_zones:
                return {
                    "success": False,
                    "error": f"Invalid zone: {zone}"
                }
            
            # Get all emotions in this zone
            zone_emotions = [
                emotion for emotion, z in self.emotion_to_zone.items()
                if z == zone
            ]
            
            # Collect tasks from all emotions in zone
            all_tasks = []
            for emotion in zone_emotions:
                emotion_data = self.recommendations.get(emotion, {})
                tasks = emotion_data.get('tasks', [])
                for task in tasks:
                    task_copy = task.copy()
                    task_copy['emotion'] = emotion
                    all_tasks.append(task_copy)
            
            # Limit count
            selected_tasks = all_tasks[:count]
            
            zone_info = self.task_zones[zone]
            
            return {
                "success": True,
                "zone": zone,
                "zone_name": zone_info.get('name', ''),
                "zone_info": zone_info,
                "emotions": zone_emotions,
                "tasks": selected_tasks,
                "count": len(selected_tasks)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting zone recommendations: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recommendation_by_stress(
        self,
        stress_score: int,
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Get recommendations based on stress score
        
        Args:
            stress_score: Stress score (0-10)
            count: Number of recommendations
        
        Returns:
            dict: Stress-appropriate recommendations
        """
        try:
            # Determine appropriate zone based on stress
            if stress_score >= 7:
                zone = 'RED'
            elif stress_score >= 5:
                zone = 'ORANGE'
            elif stress_score >= 3:
                zone = 'YELLOW'
            else:
                zone = 'GREEN'
            
            result = self.get_zone_recommendations(zone, count)
            
            if result.get('success'):
                result['stress_score'] = stress_score
                result['reasoning'] = f"Zone {zone} selected based on stress level"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting stress-based recommendation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Create global service instance
recommendation_service = RecommendationService()