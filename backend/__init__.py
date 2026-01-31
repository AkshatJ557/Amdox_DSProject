"""
Amdox Backend Package
AI-powered employee emotion, stress, and task optimization system
"""

__version__ = "1.0.0"
__author__ = "Amdox Team"

# Database management
from backend.database.db import db_manager

# Repository modules
from backend.database.user_repo import user_repo
from backend.database.mood_repo import mood_repo
from backend.database.team_repo import team_repo

# Service modules
from backend.services.stress_service import stress_service
from backend.services.recommendation_service import recommendation_service
from backend.services.alert_service import alert_service
from backend.services.aggregation_service import aggregation_service

# Controller modules
from backend.controllers.emotion_controller import emotion_controller
from backend.controllers.stress_controller import stress_controller
from backend.controllers.recommendation_controller import recommendation_controller
from backend.controllers.analytics_controller import analytics_controller

# ML modules
from backend.ml.emotion.emotion_model import emotion_model
from backend.ml.emotion.dominant_emotion import dominant_emotion_analyzer


def initialize_database():
    """
    Initialize database connection and create required indexes
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        print("🔌 Initializing database connection...")
        
        # Connect to database
        db_manager.connect()
        
        print("✅ Database connected successfully")
        print(f"   Database: {db_manager.db.name}")
        
        # Initialize indexes for all collections
        print("📑 Creating database indexes...")
        
        try:
            # Users collection indexes
            user_repo.collection.create_index("user_id", unique=True)
            user_repo.collection.create_index("email", unique=True, sparse=True)
            user_repo.collection.create_index("created_at")
            print("   ✅ Users collection indexes created")
        except Exception as e:
            print(f"   ⚠️ Warning creating user indexes: {e}")
        
        try:
            # Mood collection indexes
            mood_repo.collection.create_index("user_id")
            mood_repo.collection.create_index("session_id")
            mood_repo.collection.create_index("timestamp")
            mood_repo.collection.create_index([("user_id", 1), ("timestamp", -1)])
            print("   ✅ Mood collection indexes created")
        except Exception as e:
            print(f"   ⚠️ Warning creating mood indexes: {e}")
        
        try:
            # Team collection indexes
            team_repo.collection.create_index("team_id", unique=True)
            team_repo.collection.create_index("name")
            print("   ✅ Team collection indexes created")
        except Exception as e:
            print(f"   ⚠️ Warning creating team indexes: {e}")
        
        print("✅ Database initialization complete")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def shutdown_database():
    """Close database connection"""
    try:
        print("🔌 Closing database connection...")
        db_manager.close_connection()
        print("✅ Database connection closed")
    except Exception as e:
        print(f"⚠️ Error closing database connection: {e}")


def get_service_status():
    """
    Get status of all backend services
    
    Returns:
        dict: Service status information
    """
    return {
        "database": {
            "connected": db_manager.is_connected(),
            "database": db_manager.db.name if db_manager.is_connected() else None
        },
        "services": {
            "stress": stress_service is not None,
            "recommendation": recommendation_service is not None,
            "alert": alert_service is not None,
            "aggregation": aggregation_service is not None
        },
        "controllers": {
            "emotion": emotion_controller is not None,
            "stress": stress_controller is not None,
            "recommendation": recommendation_controller is not None,
            "analytics": analytics_controller is not None
        },
        "ml": {
            "emotion_model": emotion_model is not None and emotion_model.loaded,
            "dominant_analyzer": dominant_emotion_analyzer is not None
        }
    }


__all__ = [
    "__version__",
    "db_manager",
    "user_repo",
    "mood_repo", 
    "team_repo",
    "stress_service",
    "recommendation_service",
    "alert_service",
    "aggregation_service",
    "emotion_controller",
    "stress_controller",
    "recommendation_controller",
    "analytics_controller",
    "emotion_model",
    "dominant_emotion_analyzer",
    "initialize_database",
    "shutdown_database",
    "get_service_status"
]

