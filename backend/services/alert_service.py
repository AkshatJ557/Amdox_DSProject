"""
Alert service for monitoring and notifications
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.database.db import db_manager


class AlertService:
    """
    Service for managing alerts and notifications
    """
    
    def __init__(self):
        self.alert_cooldown_minutes = 15
        self.max_daily_alerts = 5
        self.db = db_manager.get_database()
    
    def check_and_create_alert(
        self, 
        user_id: str, 
        alert_type: str, 
        severity: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Check conditions and create an alert if conditions are met
        
        Args:
            user_id: User ID
            alert_type: Type of alert (stress, emotion, etc.)
            severity: Alert severity (low, medium, high, critical)
            message: Alert message
            metadata: Additional alert metadata
        
        Returns:
            dict: Alert result
        """
        try:
            # Check cooldown
            if self._is_in_cooldown(user_id, alert_type):
                return {
                    "success": True,
                    "alert_created": False,
                    "reason": "cooldown",
                    "message": "Alert suppressed due to recent similar alert"
                }
            
            # Check daily limit
            if self._exceeded_daily_limit(user_id):
                return {
                    "success": True,
                    "alert_created": False,
                    "reason": "daily_limit",
                    "message": "Daily alert limit reached"
                }
            
            # Create alert
            alert = {
                "user_id": user_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "acknowledged": False
            }
            
            result = self.db.alerts.insert_one(alert)
            alert["_id"] = str(result.inserted_id)
            
            return {
                "success": True,
                "alert_created": True,
                "alert": alert
            }
            
        except Exception as e:
            print(f"❌ Error creating alert: {e}")
            return {
                "success": False,
                "error": str(e),
                "alert_created": False
            }
    
    def get_user_alerts(
        self, 
        user_id: str, 
        limit: int = 20,
        acknowledged: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get alerts for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of alerts
            acknowledged: Filter by acknowledged status
        
        Returns:
            dict: User alerts
        """
        try:
            query = {"user_id": user_id}
            if acknowledged is not None:
                query["acknowledged"] = acknowledged
            
            alerts = list(
                self.db.alerts
                .find(query)
                .sort("created_at", -1)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            
            return {
                "success": True,
                "user_id": user_id,
                "alert_count": len(alerts),
                "alerts": alerts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting user alerts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID
        
        Returns:
            dict: Acknowledge result
        """
        try:
            result = self.db.alerts.update_one(
                {"_id": alert_id},
                {
                    "$set": {
                        "acknowledged": True,
                        "acknowledged_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": result.modified_count > 0,
                "message": "Alert acknowledged" if result.modified_count > 0 else "Alert not found"
            }
            
        except Exception as e:
            print(f"❌ Error acknowledging alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_in_cooldown(self, user_id: str, alert_type: str) -> bool:
        """Check if user is in cooldown for alert type"""
        try:
            cooldown_period = datetime.utcnow() - timedelta(minutes=self.alert_cooldown_minutes)
            
            recent_alert = self.db.alerts.find_one({
                "user_id": user_id,
                "alert_type": alert_type,
                "created_at": {"$gte": cooldown_period}
            })
            
            return recent_alert is not None
            
        except Exception:
            return False
    
    def _exceeded_daily_limit(self, user_id: str) -> bool:
        """Check if daily alert limit exceeded"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            count = self.db.alerts.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": today_start}
            })
            
            return count >= self.max_daily_alerts
            
        except Exception:
            return False
    
    def delete_old_alerts(self, days: int = 30) -> Dict[str, Any]:
        """
        Delete alerts older than specified days
        
        Args:
            days: Number of days to keep
        
        Returns:
            dict: Deletion result
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.db.alerts.delete_many({
                "created_at": {"$lt": cutoff_date},
                "acknowledged": True
            })
            
            return {
                "success": True,
                "deleted_count": result.deleted_count
            }
            
        except Exception as e:
            print(f"❌ Error deleting old alerts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_alert_summary(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get alert summary for user or all users
        
        Args:
            user_id: Optional user ID
        
        Returns:
            dict: Alert summary
        """
        try:
            query = {}
            if user_id:
                query["user_id"] = user_id
            
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "user_id": "$user_id",
                            "severity": "$severity"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.user_id",
                        "alerts_by_severity": {
                            "$push": {
                                "severity": "$_id.severity",
                                "count": "$count"
                            }
                        },
                        "total_count": {"$sum": "$count"}
                    }
                }
            ]
            
            results = list(self.db.alerts.aggregate(pipeline))
            
            summary = {}
            for r in results:
                user_id_key = r["_id"]
                summary[user_id_key] = {
                    "total_alerts": r["total_count"],
                    "by_severity": {
                        item["severity"]: item["count"] 
                        for item in r["alerts_by_severity"]
                    }
                }
            
            return {
                "success": True,
                "summary": summary,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting alert summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Create global service instance
alert_service = AlertService()

