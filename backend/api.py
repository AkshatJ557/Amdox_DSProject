"""
FastAPI Server for Amdox Emotion Detection System
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
import os
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import backend modules with error handling
BACKEND_IMPORTS_SUCCESSFUL = False
APP_NAME = "Amdox Emotion Detection API"
VERSION = "1.0.0"

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="AI-powered employee emotion, stress, and task optimization system",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Try to import all backend components
try:
    from backend.config import (
        APP_NAME as CONFIG_APP_NAME,
        VERSION as CONFIG_VERSION,
        EMOTION_LABELS,
        STRESS_EMOTIONS,
        SESSION_DURATION,
        STRESS_THRESHOLD
    )
    APP_NAME = CONFIG_APP_NAME
    VERSION = CONFIG_VERSION
    
    from backend.database.db import db_manager
    from backend.database.user_repo import user_repo
    from backend.database.mood_repo import mood_repo
    from backend.database.team_repo import team_repo
    
    from backend.services.stress_service import stress_service
    from backend.services.recommendation_service import recommendation_service
    from backend.services.alert_service import alert_service
    from backend.services.aggregation_service import aggregation_service
    
    from backend.controllers.emotion_controller import emotion_controller
    from backend.controllers.stress_controller import stress_controller
    from backend.controllers.recommendation_controller import recommendation_controller
    from backend.controllers.analytics_controller import analytics_controller
    
    BACKEND_IMPORTS_SUCCESSFUL = True
    logger.info("✅ All backend modules imported successfully")
    
except ImportError as e:
    logger.warning(f"⚠️ Some imports failed: {e}")
except Exception as e:
    logger.error(f"❌ Error importing backend modules: {e}")

# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    backend_loaded: bool
    database_status: Optional[str] = None
    version: str

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class EmotionSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_data: Optional[Dict[str, Any]] = None

class StressRequest(BaseModel):
    dominant_emotion: str = Field(..., description="Dominant emotion from session")
    user_id: str = Field(..., min_length=1)
    previous_score: Optional[int] = Field(None, ge=0, le=10)

class TaskRecommendationRequest(BaseModel):
    dominant_emotion: str = Field(..., description="Dominant emotion")
    stress_score: Optional[int] = Field(None, ge=0, le=10, description="Current stress score (0-10)")
    workload_level: Optional[int] = Field(None, ge=1, le=5, description="Workload level (1-5)")
    deadline_pressure: Optional[int] = Field(None, ge=1, le=5, description="Deadline pressure (1-5)")
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description="Hours of sleep")

class FrameData(BaseModel):
    session_id: str
    user_id: str
    frame_base64: Optional[str] = None

class AnalyticsRequest(BaseModel):
    days: int = Field(30, ge=1, le=365)
    team_id: Optional[str] = None

# ==================== HEALTH & STATUS ENDPOINTS ====================
@app.get("/", response_model=Dict[str, Any], tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": APP_NAME,
        "version": VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "emotion": "/emotion/*",
            "stress": "/stress/*",
            "recommendation": "/recommend/*",
            "analytics": "/analytics/*",
            "database": "/db/*"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_status = None
    backend_status = "loaded" if BACKEND_IMPORTS_SUCCESSFUL else "not_loaded"
    
    if BACKEND_IMPORTS_SUCCESSFUL:
        try:
            db_manager.client.admin.command('ping')
            db_status = "connected"
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            db_status = f"error: {str(e)[:100]}"
    
    return HealthResponse(
        status="healthy" if BACKEND_IMPORTS_SUCCESSFUL else "degraded",
        service="amdox_api",
        timestamp=datetime.utcnow().isoformat(),
        backend_loaded=BACKEND_IMPORTS_SUCCESSFUL,
        database_status=db_status,
        version=VERSION
    )

@app.get("/config", tags=["Configuration"])
async def get_config():
    """Get application configuration"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    config = {
        "app_name": APP_NAME,
        "version": VERSION,
        "emotion_labels": EMOTION_LABELS,
        "stress_emotions": STRESS_EMOTIONS,
        "session_duration": SESSION_DURATION,
        "stress_threshold": STRESS_THRESHOLD
    }
    return config

# ==================== EMOTION ENDPOINTS ====================
@app.post("/emotion/session/start", tags=["Emotion"])
async def start_emotion_session(request: EmotionSessionRequest):
    """Start a new emotion detection session"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded. Please check server logs."
        )
    
    try:
        result = emotion_controller.start_emotion_session(
            user_id=request.user_id,
            session_data=request.session_data
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to start session")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting emotion session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/emotion/session/{session_id}", tags=["Emotion"])
async def get_session_status(session_id: str):
    """Get status of an emotion session"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = emotion_controller.get_session_status(session_id)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Session not found")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/emotion/session/{session_id}/complete", tags=["Emotion"])
async def complete_session(session_id: str, user_id: str, context: Optional[Dict[str, Any]] = None):
    """Complete an emotion session and get results"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = emotion_controller.complete_session(
            session_id=session_id,
            user_id=user_id,
            context=context
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to complete session")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/emotion/validate", tags=["Emotion"])
async def validate_emotion_system():
    """Validate camera and emotion model"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        return {
            "success": False,
            "error": "Backend modules not loaded",
            "camera": {"available": False, "status": "backend_not_loaded"},
            "emotion_model": {"loaded": False}
        }
    
    try:
        result = emotion_controller.validate_camera()
        return result
    except Exception as e:
        logger.error(f"Error validating emotion system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ==================== STRESS ENDPOINTS ====================
@app.post("/stress/calculate", tags=["Stress"])
async def calculate_stress(request: StressRequest):
    """Calculate stress score based on dominant emotion"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        return {
            "success": True,
            "user_id": request.user_id,
            "dominant_emotion": request.dominant_emotion,
            "stress_analysis": {
                "stress_score": 2,
                "stress_level": "Low",
                "threshold_crossed": False,
                "previous_score": request.previous_score or 0
            },
            "mock_data": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        result = stress_controller.calculate_stress(
            dominant_emotion=request.dominant_emotion,
            user_id=request.user_id,
            previous_score=request.previous_score
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to calculate stress")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating stress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/stress/history/{user_id}", tags=["Stress"])
async def get_stress_history(user_id: str, limit: int = 20):
    """Get stress history for user"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = stress_controller.get_user_stress_history(user_id, limit)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "User not found or no history available")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stress history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/stress/trend/{user_id}", tags=["Stress"])
async def get_stress_trend(user_id: str, days: int = 7):
    """Get stress trend analysis for user"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = stress_controller.get_stress_trend(user_id, days)
        return result
    except Exception as e:
        logger.error(f"Error getting stress trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/stress/check-threshold", tags=["Stress"])
async def check_stress_threshold(score: int, user_id: Optional[str] = None):
    """Check if stress score crosses threshold"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        return {
            "success": True,
            "stress_score": score,
            "threshold": 3,
            "threshold_crossed": score >= 3,
            "mock_data": True
        }
    
    try:
        result = stress_controller.check_stress_threshold(score, user_id)
        return result
    except Exception as e:
        logger.error(f"Error checking stress threshold: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ==================== RECOMMENDATION ENDPOINTS ====================
@app.post("/recommend/task", tags=["Recommendation"])
async def recommend_task(request: TaskRecommendationRequest):
    """Get task recommendation based on emotion and context"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        return {
            "success": True,
            "dominant_emotion": request.dominant_emotion,
            "recommendation": {
                "task": "Take a short break and reassess current work",
                "category": "General",
                "priority": "Medium",
                "duration": "15-30 minutes",
                "confidence_score": 0.7
            },
            "mock_data": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        context = {}
        if request.stress_score is not None:
            context["stress_score"] = request.stress_score
        if request.workload_level is not None:
            context["workload_level"] = request.workload_level
        if request.deadline_pressure is not None:
            context["deadline_pressure"] = request.deadline_pressure
        if request.sleep_hours is not None:
            context["sleep_hours"] = request.sleep_hours
        
        result = recommendation_controller.recommend_task(
            dominant_emotion=request.dominant_emotion,
            context=context if context else None
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to generate recommendation")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/recommend/multiple/{emotion}", tags=["Recommendation"])
async def get_multiple_recommendations(emotion: str, count: int = 3):
    """Get multiple task suggestions for an emotion"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        return {
            "success": True,
            "dominant_emotion": emotion,
            "suggestions": [
                {"task": "Take a short break", "category": "General", "priority": "Medium"},
                {"task": "Review pending tasks", "category": "Administrative", "priority": "Low"},
                {"task": "Organize workspace", "category": "Productivity", "priority": "Low"}
            ][:count],
            "mock_data": True
        }
    
    try:
        result = recommendation_controller.get_multiple_recommendations(
            dominant_emotion=emotion,
            count=count
        )
        return result
    except Exception as e:
        logger.error(f"Error getting multiple recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/recommend/tasks-by-emotion", tags=["Recommendation"])
async def get_emotion_based_tasks():
    """Get all available tasks organized by emotion"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        return {
            "success": True,
            "emotion_task_mapping": {
                "Happy": {"category": "Creative", "tasks": ["Creative work"]},
                "Neutral": {"category": "General", "tasks": ["Routine tasks"]}
            },
            "mock_data": True
        }
    
    try:
        result = recommendation_controller.get_emotion_based_tasks()
        return result
    except Exception as e:
        logger.error(f"Error getting emotion-based tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ==================== ANALYTICS ENDPOINTS ====================
@app.get("/analytics/dashboard", tags=["Analytics"])
async def get_dashboard_analytics():
    """Get dashboard analytics"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = analytics_controller.get_dashboard_analytics()
        return result
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/analytics/emotion", tags=["Analytics"])
async def get_emotion_analytics(days: int = 30, team_id: Optional[str] = None):
    """Get emotion analytics report"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = analytics_controller.get_emotion_analytics_report(
            days=days,
            team_id=team_id
        )
        return result
    except Exception as e:
        logger.error(f"Error getting emotion analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/analytics/stress", tags=["Analytics"])
async def get_stress_analytics(days: int = 30, team_id: Optional[str] = None):
    """Get stress analytics report"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = analytics_controller.get_stress_analytics_report(
            days=days,
            team_id=team_id
        )
        return result
    except Exception as e:
        logger.error(f"Error getting stress analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/analytics/user/{user_id}", tags=["Analytics"])
async def get_user_analytics(user_id: str, days: int = 30):
    """Get user activity report"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = analytics_controller.get_user_activity_report(user_id, days)
        return result
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ==================== DATABASE ENDPOINTS ====================
@app.get("/db/collections", tags=["Database"])
async def list_collections():
    """List all collections in database"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        collections = db_manager.db.list_collection_names()
        return {
            "success": True,
            "database": db_manager.db.name,
            "collections": collections,
            "count": len(collections),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/db/health", tags=["Database"])
async def database_health():
    """Check database health"""
    if not BACKEND_IMPORTS_SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend modules not loaded"
        )
    
    try:
        result = db_manager.health_check()
        return result
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ==================== TEST ENDPOINTS ====================
@app.get("/test/backend", tags=["Testing"])
async def test_backend():
    """Test if backend modules are working"""
    test_results = {
        "backend_loaded": BACKEND_IMPORTS_SUCCESSFUL,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    if BACKEND_IMPORTS_SUCCESSFUL:
        try:
            db_manager.client.admin.command('ping')
            test_results["components"]["database"] = {
                "status": "✅ connected",
                "database": db_manager.db.name
            }
        except Exception as e:
            test_results["components"]["database"] = {
                "status": f"❌ {str(e)[:100]}",
                "error": str(e)
            }
        
        try:
            test_stress = stress_service.calculate_stress_score("Neutral", "test_user")
            test_results["components"]["stress_service"] = {
                "status": "✅ working",
                "test_score": test_stress.get("stress_score", "N/A")
            }
        except Exception as e:
            test_results["components"]["stress_service"] = {
                "status": f"❌ {str(e)[:100]}",
                "error": str(e)
            }
        
        try:
            test_emotion = emotion_controller.start_emotion_session("test_user")
            test_results["components"]["emotion_controller"] = {
                "status": "✅ working",
                "session_id": test_emotion.get("session_id", "N/A")
            }
        except Exception as e:
            test_results["components"]["emotion_controller"] = {
                "status": f"❌ {str(e)[:100]}",
                "error": str(e)
            }
        
        try:
            test_recommendation = recommendation_service.recommend_task("Happy")
            test_results["components"]["recommendation_service"] = {
                "status": "✅ working",
                "test_task": test_recommendation.get("task", "N/A")
            }
        except Exception as e:
            test_results["components"]["recommendation_service"] = {
                "status": f"❌ {str(e)[:100]}",
                "error": str(e)
            }
    else:
        test_results["components"] = {"message": "Backend modules not loaded"}
    
    return test_results

# ==================== ERROR HANDLERS ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if BACKEND_IMPORTS_SUCCESSFUL else "Backend modules not loaded",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ==================== STARTUP & SHUTDOWN ====================
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("\n" + "="*60)
    print("🚀 Starting Amdox Emotion Detection Backend Server")
    print("="*60)
    print(f"📡 API: http://localhost:8080")
    print(f"📚 Documentation: http://localhost:8080/docs")
    print(f"🏥 Health Check: http://localhost:8080/health")
    print(f"🔧 Test Backend: http://localhost:8080/test/backend")
    print("="*60)
    
    if BACKEND_IMPORTS_SUCCESSFUL:
        try:
            print("🔌 Initializing database connection...")
            db_manager.connect()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"⚠️ Error during startup: {e}")
    else:
        print("⚠️ Running in limited mode - some backend modules not loaded")
        print("💡 Check that all dependencies are installed and config files exist")
    
    print("✅ Server is ready to accept requests")
    print("="*60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n👋 Shutting down Amdox Backend Server...")
    if BACKEND_IMPORTS_SUCCESSFUL:
        try:
            db_manager.close_connection()
            print("✅ Database connection closed")
        except:
            pass
    print("✅ Server shutdown complete")

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
        access_log=True
    )

