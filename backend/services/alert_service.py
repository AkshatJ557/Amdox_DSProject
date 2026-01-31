"""
Enhanced Alert Service for Amdox
Production-grade alert management with cooldown, daily limits, and severity handling
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


class AlertService:
    """
    Enhanced Alert Service with intelligent cooldown and severity management
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.cooldown_minutes = 15  # Cooldown period between alerts
        self.daily_limit = 5  # Maximum alerts per user per day
        self._alert_cache = defaultdict(list)  # In-memory cache
        logger.info("🚨 Alert Service initialized")
    
    def check_and_create_alert(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Check conditions and create alert if appropriate
        
        Args:
            user_id: User ID
            alert_type: Alert type (high_stress, critical_stress, etc.)
            severity: Severity level (low/medium/high/critical)
            message: Alert message
            metadata: Additional metadata
        
        Returns:
            dict: Alert creation result
        """
        try:
            # Validate severity
            valid_severities = ['low', 'medium', 'high', 'critical']
            if severity not in valid_severities:
                return {
                    "success": False,
                    "error": f"Invalid severity. Must be one of: {valid_severities}"
                }
            
            # Check cooldown
            if self._is_in_cooldown(user_id, alert_type):
                logger.info(f"⏰ Alert for {user_id} is in cooldown period")
                return {
                    "success": True,
                    "alert_created": False,
                    "reason": "cooldown_active",
                    "message": f"Alert cooldown active ({self.cooldown_minutes} min)"
                }
            
            # Check daily limit
            if self._exceeds_daily_limit(user_id):
                logger.warning(f"⚠️ Daily alert limit reached for {user_id}")
                return {
                    "success": True,
                    "alert_created": False,
                    "reason": "daily_limit_reached",
                    "message": f"Daily alert limit ({self.daily_limit}) reached"
                }
            
            # Create alert
            alert = self._create_alert(
                user_id,
                alert_type,
                severity,
                message,
                metadata
            )
            
            logger.info(f"🚨 Alert created for {user_id}: {alert_type} ({severity})")
            
            return {
                "success": True,
                "alert_created": True,
                "alert": alert
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_in_cooldown(self, user_id: str, alert_type: str) -> bool:
        """
        Check if user is in cooldown period for alert type
        
        Args:
            user_id: User ID
            alert_type: Alert type
        
        Returns:
            bool: True if in cooldown
        """
        try:
            cooldown_time = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)
            
            # Check database
            recent_alert = self.db.alerts.find_one({
                "user_id": user_id,
                "alert_type": alert_type,
                "created_at": {"$gte": cooldown_time}
            })
            
            return recent_alert is not None
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False
    
    def _exceeds_daily_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded daily alert limit
        
        Args:
            user_id: User ID
        
        Returns:
            bool: True if limit exceeded
        """
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Count today's alerts
            alert_count = self.db.alerts.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": today_start}
            })
            
            return alert_count >= self.daily_limit
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return False
    
    def _create_alert(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Create and save alert to database
        
        Args:
            user_id: User ID
            alert_type: Alert type
            severity: Severity level
            message: Alert message
            metadata: Additional metadata
        
        Returns:
            dict: Created alert document
        """
        try:
            alert = {
                "user_id": user_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "metadata": metadata or {},
                "acknowledged": False,
                "acknowledged_at": None,
                "created_at": datetime.utcnow(),
                "expires_at": self._calculate_expiry(severity)
            }
            
            # Save to database
            result = self.db.alerts.insert_one(alert)
            alert["_id"] = str(result.inserted_id)
            
            # Cache in memory
            self._alert_cache[user_id].append({
                "alert_id": str(result.inserted_id),
                "created_at": alert["created_at"],
                "alert_type": alert_type
            })
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert document: {e}")
            raise
    
    def _calculate_expiry(self, severity: str) -> datetime:
        """Calculate alert expiry time based on severity"""
        expiry_hours = {
            'low': 24,
            'medium': 48,
            'high': 72,
            'critical': 168  # 1 week
        }
        
        hours = expiry_hours.get(severity, 24)
        return datetime.utcnow() + timedelta(hours=hours)
    
    def get_user_alerts(
        self,
        user_id: str,
        include_acknowledged: bool = False,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get alerts for a user
        
        Args:
            user_id: User ID
            include_acknowledged: Include acknowledged alerts
            limit: Maximum alerts to return
        
        Returns:
            dict: User alerts
        """
        try:
            query = {"user_id": user_id}
            
            if not include_acknowledged:
                query["acknowledged"] = False
            
            alerts = list(
                self.db.alerts
                .find(query)
                .sort("created_at", -1)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            
            # Group by severity
            by_severity = defaultdict(list)
            for alert in alerts:
                by_severity[alert["severity"]].append(alert)
            
            return {
                "success": True,
                "user_id": user_id,
                "alerts": alerts,
                "total_count": len(alerts),
                "unacknowledged_count": sum(1 for a in alerts if not a.get("acknowledged")),
                "by_severity": dict(by_severity)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user alerts: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
        acknowledgement_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID
            user_id: User ID (for verification)
            acknowledgement_note: Optional note
        
        Returns:
            dict: Acknowledgement result
        """
        try:
            from bson import ObjectId
            
            # Verify alert belongs to user
            alert = self.db.alerts.find_one({
                "_id": ObjectId(alert_id),
                "user_id": user_id
            })
            
            if not alert:
                return {
                    "success": False,
                    "error": "Alert not found or does not belong to user"
                }
            
            if alert.get("acknowledged"):
                return {
                    "success": True,
                    "message": "Alert already acknowledged",
                    "acknowledged_at": alert.get("acknowledged_at")
                }
            
            # Update alert
            update_data = {
                "acknowledged": True,
                "acknowledged_at": datetime.utcnow(),
                "acknowledgement_note": acknowledgement_note
            }
            
            self.db.alerts.update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": update_data}
            )
            
            logger.info(f"✅ Alert {alert_id} acknowledged by {user_id}")
            
            return {
                "success": True,
                "alert_id": alert_id,
                "acknowledged_at": update_data["acknowledged_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error acknowledging alert: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_team_alerts(
        self,
        team_id: str,
        severity_filter: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get alerts for all team members
        
        Args:
            team_id: Team ID
            severity_filter: Optional severity filter
            limit: Maximum alerts
        
        Returns:
            dict: Team alerts
        """
        try:
            # Get team members
            team = self.db.teams.find_one({"team_id": team_id})
            
            if not team:
                return {
                    "success": False,
                    "error": f"Team {team_id} not found"
                }
            
            member_ids = team.get("members", [])
            
            if not member_ids:
                return {
                    "success": True,
                    "team_id": team_id,
                    "alerts": [],
                    "message": "No team members found"
                }
            
            # Build query
            query = {
                "user_id": {"$in": member_ids},
                "acknowledged": False
            }
            
            if severity_filter:
                query["severity"] = severity_filter
            
            # Get alerts
            alerts = list(
                self.db.alerts
                .find(query)
                .sort("created_at", -1)
                .limit(limit)
            )
            
            # Convert ObjectIds
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            
            # Statistics
            severity_counts = defaultdict(int)
            user_counts = defaultdict(int)
            
            for alert in alerts:
                severity_counts[alert["severity"]] += 1
                user_counts[alert["user_id"]] += 1
            
            return {
                "success": True,
                "team_id": team_id,
                "team_name": team.get("name"),
                "alerts": alerts,
                "total_count": len(alerts),
                "severity_breakdown": dict(severity_counts),
                "users_with_alerts": len(user_counts),
                "high_priority_count": severity_counts.get("high", 0) + severity_counts.get("critical", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting team alerts: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_old_alerts(self, days: int = 30) -> Dict[str, Any]:
        """
        Delete old acknowledged alerts
        
        Args:
            days: Delete alerts older than this many days
        
        Returns:
            dict: Deletion result
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.db.alerts.delete_many({
                "acknowledged": True,
                "acknowledged_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"🗑️ Deleted {result.deleted_count} old alerts")
            
            return {
                "success": True,
                "deleted_count": result.deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting old alerts: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_alert_statistics(
        self,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get alert statistics
        
        Args:
            user_id: Optional user ID filter
            team_id: Optional team ID filter
            days: Number of days to analyze
        
        Returns:
            dict: Alert statistics
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            query = {"created_at": {"$gte": since}}
            
            # Apply filters
            if user_id:
                query["user_id"] = user_id
            elif team_id:
                team = self.db.teams.find_one({"team_id": team_id})
                if team:
                    query["user_id"] = {"$in": team.get("members", [])}
            
            # Get alerts
            alerts = list(self.db.alerts.find(query))
            
            if not alerts:
                return {
                    "success": True,
                    "period_days": days,
                    "message": "No alerts in period",
                    "statistics": {}
                }
            
            # Calculate statistics
            total = len(alerts)
            acknowledged = sum(1 for a in alerts if a.get("acknowledged"))
            
            severity_counts = defaultdict(int)
            type_counts = defaultdict(int)
            
            for alert in alerts:
                severity_counts[alert["severity"]] += 1
                type_counts[alert["alert_type"]] += 1
            
            # Response time (time to acknowledge)
            response_times = []
            for alert in alerts:
                if alert.get("acknowledged") and alert.get("acknowledged_at"):
                    delta = (alert["acknowledged_at"] - alert["created_at"]).total_seconds() / 60
                    response_times.append(delta)
            
            avg_response = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "success": True,
                "period_days": days,
                "statistics": {
                    "total_alerts": total,
                    "acknowledged": acknowledged,
                    "unacknowledged": total - acknowledged,
                    "acknowledgement_rate": round((acknowledged / total) * 100, 1) if total > 0 else 0,
                    "severity_breakdown": dict(severity_counts),
                    "type_breakdown": dict(type_counts),
                    "avg_response_time_minutes": round(avg_response, 1),
                    "critical_count": severity_counts.get("critical", 0),
                    "high_count": severity_counts.get("high", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting alert statistics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def set_cooldown_period(self, minutes: int):
        """Set alert cooldown period"""
        if minutes < 1 or minutes > 60:
            logger.error("Cooldown must be between 1 and 60 minutes")
            return
        
        self.cooldown_minutes = minutes
        logger.info(f"✅ Cooldown period set to {minutes} minutes")
    
    def set_daily_limit(self, limit: int):
        """Set daily alert limit"""
        if limit < 1 or limit > 20:
            logger.error("Daily limit must be between 1 and 20")
            return
        
        self.daily_limit = limit
        logger.info(f"✅ Daily alert limit set to {limit}")


# Create global service instance
alert_service = AlertService()