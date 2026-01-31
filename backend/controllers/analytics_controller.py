"""
Enhanced Analytics Controller for Amdox
Production-grade analytics with caching, validation, and comprehensive reporting
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
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

from backend.database.db import db_manager
from backend.services.aggregation_service import aggregation_service


class AnalyticsController:
    """
    Enhanced Controller for analytics and reporting endpoints
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
        logger.info("✅ Analytics Controller initialized")
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                logger.info(f"📦 Cache hit for key: {key}")
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """Set cache with timestamp"""
        self._cache[key] = (data, datetime.utcnow())
        logger.info(f"💾 Cache set for key: {key}")
    
    def get_dashboard_analytics(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive dashboard analytics summary
        
        Args:
            use_cache: Whether to use cached data
        
        Returns:
            dict: Dashboard analytics with metrics and trends
        """
        cache_key = "dashboard_analytics"
        
        # Check cache
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            logger.info("📊 Generating dashboard analytics...")
            
            # Get basic counts
            users_count = self.db.users.count_documents({})
            teams_count = self.db.teams.count_documents({})
            mood_entries_count = self.db.mood_entries.count_documents({})
            
            # Get recent activity (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_entries = self.db.mood_entries.count_documents({
                "timestamp": {"$gte": last_24h}
            })
            
            # Get active users (users with entries in last 7 days)
            last_7d = datetime.utcnow() - timedelta(days=7)
            active_users_pipeline = [
                {"$match": {"timestamp": {"$gte": last_7d}}},
                {"$group": {"_id": "$user_id"}},
                {"$count": "active_users"}
            ]
            active_users_result = list(self.db.mood_entries.aggregate(active_users_pipeline))
            active_users = active_users_result[0]["active_users"] if active_users_result else 0
            
            # Get emotion distribution (last 7 days)
            emotion_pipeline = [
                {"$match": {"timestamp": {"$gte": last_7d}}},
                {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            emotion_results = list(self.db.mood_entries.aggregate(emotion_pipeline))
            
            emotion_distribution = {
                r["_id"]: r["count"] for r in emotion_results
            }
            
            # Calculate percentages
            total_emotions = sum(emotion_distribution.values())
            emotion_percentages = {
                emotion: round((count / total_emotions) * 100, 2) if total_emotions > 0 else 0
                for emotion, count in emotion_distribution.items()
            }
            
            # Calculate average stress
            stress_pipeline = [
                {"$match": {"timestamp": {"$gte": last_7d}}},
                {"$group": {
                    "_id": None, 
                    "avg_stress": {"$avg": "$stress_score"},
                    "max_stress": {"$max": "$stress_score"},
                    "min_stress": {"$min": "$stress_score"}
                }}
            ]
            stress_result = list(self.db.mood_entries.aggregate(stress_pipeline))
            
            if stress_result:
                avg_stress = round(stress_result[0]["avg_stress"], 2)
                max_stress = stress_result[0]["max_stress"]
                min_stress = stress_result[0]["min_stress"]
            else:
                avg_stress = max_stress = min_stress = 0
            
            # Get high stress count (score >= 7)
            high_stress_count = self.db.mood_entries.count_documents({
                "timestamp": {"$gte": last_7d},
                "stress_score": {"$gte": 7}
            })
            
            # Get alerts count
            alerts_count = self.db.alerts.count_documents({
                "created_at": {"$gte": last_7d},
                "acknowledged": False
            })
            
            # Calculate wellness score (0-100)
            wellness_score = self._calculate_wellness_score(
                emotion_distribution, 
                avg_stress, 
                high_stress_count,
                total_emotions
            )
            
            # Prepare response
            result = {
                "success": True,
                "dashboard": {
                    "overview": {
                        "total_users": users_count,
                        "active_users_7d": active_users,
                        "total_teams": teams_count,
                        "total_mood_entries": mood_entries_count,
                        "recent_24h_entries": recent_entries,
                        "wellness_score": wellness_score
                    },
                    "emotion_analytics": {
                        "distribution": emotion_distribution,
                        "percentages": emotion_percentages,
                        "dominant": max(emotion_distribution.items(), key=lambda x: x[1])[0] if emotion_distribution else "Unknown",
                        "total_detections": total_emotions
                    },
                    "stress_analytics": {
                        "average_stress_last_7d": avg_stress,
                        "max_stress": max_stress,
                        "min_stress": min_stress,
                        "high_stress_count": high_stress_count,
                        "high_stress_percentage": round((high_stress_count / total_emotions) * 100, 2) if total_emotions > 0 else 0
                    },
                    "alerts": {
                        "unacknowledged_count": alerts_count,
                        "severity_breakdown": self._get_alert_severity_breakdown(last_7d)
                    },
                    "trends": self._get_emotion_trends(last_7d),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Cache result
            self._set_cache(cache_key, result)
            
            logger.info("✅ Dashboard analytics generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard analytics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _calculate_wellness_score(
        self, 
        emotion_dist: Dict, 
        avg_stress: float,
        high_stress_count: int,
        total_emotions: int
    ) -> int:
        """Calculate overall wellness score (0-100)"""
        try:
            score = 100
            
            # Deduct for negative emotions
            negative_emotions = ['Sad', 'Angry', 'Fear', 'Disgust']
            negative_count = sum(emotion_dist.get(e, 0) for e in negative_emotions)
            negative_percentage = (negative_count / total_emotions * 100) if total_emotions > 0 else 0
            
            score -= (negative_percentage * 0.3)  # 30% weight
            
            # Deduct for high stress
            score -= (avg_stress * 5)  # 0-50 points based on stress
            
            # Deduct for high stress incidents
            if total_emotions > 0:
                high_stress_percentage = (high_stress_count / total_emotions) * 100
                score -= (high_stress_percentage * 0.2)  # 20% weight
            
            # Ensure score is between 0-100
            return max(0, min(100, int(score)))
            
        except Exception:
            return 50  # Default middle score if calculation fails
    
    def _get_alert_severity_breakdown(self, since: datetime) -> Dict:
        """Get alert count by severity"""
        try:
            pipeline = [
                {"$match": {"created_at": {"$gte": since}}},
                {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
            ]
            results = list(self.db.alerts.aggregate(pipeline))
            return {r["_id"]: r["count"] for r in results}
        except Exception:
            return {}
    
    def _get_emotion_trends(self, since: datetime) -> Dict:
        """Get emotion trends over time"""
        try:
            pipeline = [
                {"$match": {"timestamp": {"$gte": since}}},
                {
                    "$group": {
                        "_id": {
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                            "emotion": "$dominant_emotion"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.date": 1}}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            # Organize by date
            trends = defaultdict(dict)
            for r in results:
                date = r["_id"]["date"]
                emotion = r["_id"]["emotion"]
                trends[date][emotion] = r["count"]
            
            return dict(trends)
            
        except Exception:
            return {}
    
    def get_emotion_analytics_report(
        self, 
        days: int = 30, 
        team_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive emotion analytics report
        
        Args:
            days: Number of days to analyze
            team_id: Optional team ID to filter by
            user_id: Optional user ID to filter by
        
        Returns:
            dict: Emotion analytics report
        """
        try:
            logger.info(f"📊 Generating emotion analytics for {days} days...")
            
            # Validate inputs
            if days < 1 or days > 365:
                return {
                    "success": False,
                    "error": "Days must be between 1 and 365"
                }
            
            result = aggregation_service.aggregate_emotion_distribution(team_id, days)
            
            # Enrich with additional insights
            if result.get("success") and result.get("distribution"):
                result["insights"] = self._generate_emotion_insights(result["distribution"])
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting emotion analytics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_emotion_insights(self, distribution: Dict) -> List[str]:
        """Generate insights from emotion distribution"""
        insights = []
        
        try:
            total = sum(d["count"] for d in distribution.values())
            
            # Positive emotion percentage
            positive = ['Happy', 'Surprise']
            positive_count = sum(distribution.get(e, {}).get("count", 0) for e in positive)
            positive_pct = (positive_count / total * 100) if total > 0 else 0
            
            if positive_pct > 60:
                insights.append("🌟 Team shows strong positive emotion trends")
            elif positive_pct < 30:
                insights.append("⚠️ Low positive emotion levels detected - consider wellness initiatives")
            
            # Negative emotion percentage
            negative = ['Sad', 'Angry', 'Fear', 'Disgust']
            negative_count = sum(distribution.get(e, {}).get("count", 0) for e in negative)
            negative_pct = (negative_count / total * 100) if total > 0 else 0
            
            if negative_pct > 40:
                insights.append("🚨 High negative emotion levels - immediate intervention recommended")
            
            # Dominant emotion
            if distribution:
                dominant = max(distribution.items(), key=lambda x: x[1]["count"])
                if dominant[1]["count"] / total > 0.5:
                    insights.append(f"📊 {dominant[0]} is heavily dominant ({dominant[1]['percentage']:.1f}%)")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights if insights else ["No significant insights detected"]
    
    def get_stress_analytics_report(
        self, 
        days: int = 30, 
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get stress analytics report
        
        Args:
            days: Number of days to analyze
            team_id: Optional team ID to filter by
        
        Returns:
            dict: Stress analytics report
        """
        try:
            logger.info(f"📊 Generating stress analytics for {days} days...")
            
            result = aggregation_service.aggregate_team_stress(team_id, days)
            
            # Add stress level recommendations
            if result.get("success") and result.get("data"):
                avg_stress = result["data"].get("overall_avg_stress", 0)
                result["recommendations"] = self._get_stress_recommendations(avg_stress)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting stress analytics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_stress_recommendations(self, avg_stress: float) -> List[str]:
        """Get recommendations based on average stress"""
        recommendations = []
        
        if avg_stress >= 7:
            recommendations.extend([
                "🚨 URGENT: Implement immediate stress reduction programs",
                "👥 Schedule 1-on-1 meetings with high-stress individuals",
                "🧘 Organize wellness workshops and mindfulness sessions",
                "📊 Review workload distribution across team"
            ])
        elif avg_stress >= 5:
            recommendations.extend([
                "⚠️ Moderate stress detected - monitor closely",
                "💡 Consider introducing flexible work arrangements",
                "🎯 Review upcoming deadlines and priorities",
                "☕ Encourage regular breaks and time off"
            ])
        elif avg_stress >= 3:
            recommendations.extend([
                "✅ Stress levels are manageable",
                "📈 Continue monitoring stress trends",
                "🌟 Maintain current wellness initiatives"
            ])
        else:
            recommendations.extend([
                "🎉 Excellent stress management!",
                "✨ Team is thriving - keep it up",
                "💪 Share best practices with other teams"
            ])
        
        return recommendations
    
    def get_user_activity_report(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive user activity report
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            dict: User activity report
        """
        try:
            logger.info(f"📊 Generating user activity report for {user_id}...")
            
            if not user_id:
                return {
                    "success": False,
                    "error": "user_id is required"
                }
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get mood entries
            entries = list(
                self.db.mood_entries
                .find({"user_id": user_id, "timestamp": {"$gte": start_date}})
                .sort("timestamp", -1)
            )
            
            if not entries:
                return {
                    "success": True,
                    "message": "No activity data available",
                    "user_id": user_id,
                    "report": {
                        "total_entries": 0,
                        "emotion_distribution": {},
                        "avg_stress": 0,
                        "activity_by_day": {},
                        "wellness_score": 0
                    }
                }
            
            # Calculate emotion distribution
            from collections import Counter
            emotion_counter = Counter(e.get("dominant_emotion", "Unknown") for e in entries)
            
            # Calculate stress over time
            stress_scores = [e.get("stress_score", 0) for e in entries]
            avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
            max_stress = max(stress_scores) if stress_scores else 0
            min_stress = min(stress_scores) if stress_scores else 0
            
            # Activity by day
            activity_by_day = defaultdict(int)
            for entry in entries:
                day = entry.get("timestamp", datetime.utcnow()).strftime("%Y-%m-%d")
                activity_by_day[day] += 1
            
            # Get stress patterns
            stress_patterns = aggregation_service.analyze_stress_patterns(user_id, days)
            
            # Calculate user wellness score
            user_wellness = self._calculate_wellness_score(
                dict(emotion_counter),
                avg_stress,
                sum(1 for s in stress_scores if s >= 7),
                len(entries)
            )
            
            # Get recent sessions
            recent_sessions = self._get_recent_sessions(user_id, 5)
            
            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "report": {
                    "summary": {
                        "total_entries": len(entries),
                        "avg_stress": round(avg_stress, 2),
                        "max_stress": max_stress,
                        "min_stress": min_stress,
                        "wellness_score": user_wellness,
                        "most_common_emotion": emotion_counter.most_common(1)[0][0] if emotion_counter else "Unknown"
                    },
                    "emotion_distribution": dict(emotion_counter),
                    "activity_by_day": dict(sorted(activity_by_day.items())),
                    "stress_analysis": stress_patterns.get("analysis", {}),
                    "recent_sessions": recent_sessions,
                    "recommendations": self._get_user_recommendations(
                        avg_stress, 
                        dict(emotion_counter), 
                        len(entries)
                    )
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user activity report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_recent_sessions(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent emotion detection sessions"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": "$session_id",
                        "timestamp": {"$first": "$timestamp"},
                        "dominant_emotion": {"$first": "$dominant_emotion"},
                        "stress_score": {"$first": "$stress_score"},
                        "entry_count": {"$sum": 1}
                    }
                },
                {"$sort": {"timestamp": -1}},
                {"$limit": limit}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            return [
                {
                    "session_id": r["_id"],
                    "timestamp": r["timestamp"].isoformat(),
                    "dominant_emotion": r["dominant_emotion"],
                    "stress_score": r["stress_score"],
                    "entry_count": r["entry_count"]
                }
                for r in results
            ]
            
        except Exception:
            return []
    
    def _get_user_recommendations(
        self, 
        avg_stress: float, 
        emotions: Dict, 
        total_entries: int
    ) -> List[str]:
        """Generate personalized user recommendations"""
        recommendations = []
        
        try:
            # Stress-based recommendations
            if avg_stress >= 7:
                recommendations.append("🚨 Your stress levels are high - please reach out to HR")
                recommendations.append("🧘 Practice daily meditation (10-15 minutes)")
            elif avg_stress >= 5:
                recommendations.append("⚠️ Monitor your stress levels closely")
                recommendations.append("☕ Take regular breaks throughout the day")
            
            # Activity-based recommendations
            if total_entries < 10:
                recommendations.append("📊 Use the system more regularly for better insights")
            
            # Emotion-based recommendations
            negative_emotions = ['Sad', 'Angry', 'Fear', 'Disgust']
            negative_count = sum(emotions.get(e, 0) for e in negative_emotions)
            
            if negative_count / total_entries > 0.4:
                recommendations.append("💡 Consider speaking with a wellness counselor")
                recommendations.append("🤝 Connect with team members for support")
            
        except Exception as e:
            logger.error(f"Error generating user recommendations: {e}")
        
        return recommendations if recommendations else ["Keep up the great work! 🌟"]
    
    def get_team_report(
        self, 
        team_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive team report
        
        Args:
            team_id: Team ID
            days: Number of days to analyze
        
        Returns:
            dict: Team report
        """
        try:
            logger.info(f"📊 Generating team report for {team_id}...")
            
            result = aggregation_service.generate_team_report(team_id, days)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting team report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trending_emotions(
        self, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get trending emotions over time
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: Trending emotions
        """
        try:
            logger.info(f"📊 Getting emotion trends for {days} days...")
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": {
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                            "emotion": "$dominant_emotion"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.date": 1, "count": -1}}
            ]
            
            results = list(self.db.mood_entries.aggregate(pipeline))
            
            # Organize by date
            by_date = defaultdict(list)
            for r in results:
                date = r["_id"]["date"]
                emotion = r["_id"]["emotion"]
                by_date[date].append({
                    "emotion": emotion,
                    "count": r["count"]
                })
            
            return {
                "success": True,
                "period_days": days,
                "trends": dict(by_date),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting trending emotions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_cache(self):
        """Clear analytics cache"""
        self._cache.clear()
        logger.info("🗑️ Analytics cache cleared")


# Create global controller instance
analytics_controller = AnalyticsController()