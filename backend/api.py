"""
Enhanced FastAPI Application for Amdox
Production-grade REST API with comprehensive endpoints and validation
"""
from fastapi import FastAPI, HTTPException, status, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import controllers
from backend.controllers.analytics_controller import analytics_controller
from backend.controllers.emotion_controller import emotion_controller
from backend.controllers.recommendation_controller import recommendation_controller
from backend.controllers.stress_controller import stress_controller

# Import database
from backend.database.db import init_db, close_db, db_manager

# Import config
from backend.config import (
    API_HOST,
    API_PORT,
    CORS_ORIGINS,
    EMOTION_LABELS,
    TASK_ZONES
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EmotionSessionStart(BaseModel):
    user_id: str = Field(..., description="User ID")
    duration_minutes: int = Field(20, ge=1, le=120, description="Session duration")
    session_data: Optional[Dict[str, Any]] = None

class EmotionFrameProcess(BaseModel):
    session_id: str = Field(..., description="Session ID")
    frame_base64: Optional[str] = None
    image_bytes: Optional[bytes] = None

class SessionComplete(BaseModel):
    session_id: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    save_to_db: bool = True

class StressCalculation(BaseModel):
    dominant_emotion: str = Field(..., description="Detected emotion")
    user_id: str
    workload_level: Optional[int] = Field(None, ge=0, le=10)
    deadline_pressure: Optional[int] = Field(None, ge=0, le=10)
    working_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    
    @validator('dominant_emotion')
    def validate_emotion(cls, v):
        if v not in EMOTION_LABELS:
            raise ValueError(f"Invalid emotion. Must be one of: {EMOTION_LABELS}")
        return v

class RecommendationRequest(BaseModel):
    dominant_emotion: str
    stress_score: Optional[int] = Field(None, ge=0, le=10)
    workload_level: Optional[int] = Field(None, ge=0, le=10)
    deadline_pressure: Optional[int] = Field(None, ge=0, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    working_hours: Optional[float] = Field(None, ge=0, le=24)
    time_of_day: Optional[str] = None
    
    @validator('dominant_emotion')
    def validate_emotion(cls, v):
        if v not in EMOTION_LABELS:
            raise ValueError(f"Invalid emotion. Must be one of: {EMOTION_LABELS}")
        return v

class AlertCreate(BaseModel):
    user_id: str
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    message: str
    metadata: Optional[Dict[str, Any]] = None

class AlertAcknowledge(BaseModel):
    alert_id: str
    user_id: str
    acknowledgement_note: Optional[str] = None

class UserCreate(BaseModel):
    user_id: str
    name: str
    email: str
    password: Optional[str] = None
    role: str = Field("employee", pattern="^(employee|manager|hr|admin)$")
    team_id: Optional[str] = None

class TeamCreate(BaseModel):
    team_id: str
    name: str
    manager_id: Optional[str] = None
    members: Optional[List[str]] = []

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Amdox Emotion Detection API",
    description="AI-Powered Task Optimizer with Emotion Detection and Stress Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Starting Amdox API...")
    try:
        init_db()
        logger.info("✅ API started successfully")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database on shutdown"""
    logger.info("👋 Shutting down Amdox API...")
    close_db()

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Amdox Emotion Detection API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        db_health = db_manager.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_health.get("status"),
            "services": {
                "emotion_detection": emotion_controller.model.loaded if emotion_controller.model else False,
                "analytics": True,
                "recommendations": True,
                "stress_analysis": True,
                "alerts": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/db/status", tags=["Database"])
async def database_status():
    """Get database status"""
    try:
        health = db_manager.health_check()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EMOTION DETECTION ENDPOINTS
# ============================================================================

@app.post("/emotion/session/start", tags=["Emotion Detection"])
async def start_emotion_session(data: EmotionSessionStart):
    """Start a new emotion detection session"""
    try:
        result = emotion_controller.start_emotion_session(
            user_id=data.user_id,
            session_data=data.session_data,
            duration_minutes=data.duration_minutes
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emotion/session/{session_id}/status", tags=["Emotion Detection"])
async def get_session_status(session_id: str):
    """Get status of an emotion detection session"""
    try:
        result = emotion_controller.get_session_status(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emotion/session/{session_id}/pause", tags=["Emotion Detection"])
async def pause_session(session_id: str, user_id: str = Body(..., embed=True)):
    """Pause an active session"""
    try:
        result = emotion_controller.pause_session(session_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emotion/session/{session_id}/resume", tags=["Emotion Detection"])
async def resume_session(session_id: str, user_id: str = Body(..., embed=True)):
    """Resume a paused session"""
    try:
        result = emotion_controller.resume_session(session_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emotion/session/complete", tags=["Emotion Detection"])
async def complete_session(data: SessionComplete):
    """Complete an emotion detection session"""
    try:
        result = emotion_controller.complete_session(
            session_id=data.session_id,
            user_id=data.user_id,
            context=data.context,
            save_to_db=data.save_to_db
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emotion/validate_camera", tags=["Emotion Detection"])
async def validate_camera():
    """Validate camera and model availability"""
    try:
        result = emotion_controller.validate_camera()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emotion/session/{session_id}/statistics", tags=["Emotion Detection"])
async def get_session_statistics(session_id: str):
    """Get real-time statistics for a session"""
    try:
        result = emotion_controller.get_session_statistics(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STRESS CALCULATION ENDPOINTS
# ============================================================================

@app.post("/stress/calculate", tags=["Stress Analysis"])
async def calculate_stress(data: StressCalculation):
    """Calculate stress score with context"""
    try:
        context = {}
        if data.workload_level is not None:
            context["workload_level"] = data.workload_level
        if data.deadline_pressure is not None:
            context["deadline_pressure"] = data.deadline_pressure
        if data.working_hours is not None:
            context["working_hours"] = data.working_hours
        if data.sleep_hours is not None:
            context["sleep_hours"] = data.sleep_hours
        
        result = stress_controller.calculate_stress(
            dominant_emotion=data.dominant_emotion,
            user_id=data.user_id,
            additional_factors=context if context else None
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stress/history/{user_id}", tags=["Stress Analysis"])
async def get_stress_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    include_analytics: bool = True
):
    """Get stress history for a user"""
    try:
        result = stress_controller.get_user_stress_history(
            user_id=user_id,
            limit=limit,
            include_analytics=include_analytics
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stress/trend/{user_id}", tags=["Stress Analysis"])
async def get_stress_trend(
    user_id: str,
    days: int = Query(7, ge=1, le=90),
    granularity: str = Query("daily", pattern="^(hourly|daily|weekly)$")
):
    """Get stress trend analysis"""
    try:
        result = stress_controller.get_stress_trend(
            user_id=user_id,
            days=days,
            granularity=granularity
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stress/threshold", tags=["Stress Analysis"])
async def check_stress_threshold(
    score: int = Query(..., ge=0, le=10),
    user_id: Optional[str] = None
):
    """Check stress threshold"""
    try:
        result = stress_controller.check_stress_threshold(
            score=score,
            user_id=user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stress/recommendation", tags=["Stress Analysis"])
async def get_stress_recommendation(
    stress_score: int = Query(..., ge=0, le=10),
    user_id: Optional[str] = None
):
    """Get stress management recommendations"""
    try:
        result = stress_controller.get_stress_recommendation(
            stress_score=stress_score,
            user_id=user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@app.post("/recommend/task", tags=["Recommendations"])
async def recommend_task(data: RecommendationRequest):
    """Get task recommendation based on emotion and context"""
    try:
        context = {}
        if data.stress_score is not None:
            context["stress_score"] = data.stress_score
        if data.workload_level is not None:
            context["workload_level"] = data.workload_level
        if data.deadline_pressure is not None:
            context["deadline_pressure"] = data.deadline_pressure
        if data.sleep_hours is not None:
            context["sleep_hours"] = data.sleep_hours
        if data.working_hours is not None:
            context["working_hours"] = data.working_hours
        if data.time_of_day:
            context["time_of_day"] = data.time_of_day
        
        result = recommendation_controller.recommend_task(
            dominant_emotion=data.dominant_emotion,
            context=context if context else None
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/multiple/{emotion}", tags=["Recommendations"])
async def get_multiple_recommendations(
    emotion: str,
    count: int = Query(3, ge=1, le=10)
):
    """Get multiple task recommendations"""
    try:
        if emotion not in EMOTION_LABELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid emotion. Must be one of: {EMOTION_LABELS}"
            )
        
        result = recommendation_controller.get_multiple_recommendations(
            dominant_emotion=emotion,
            count=count
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/tasks", tags=["Recommendations"])
async def get_emotion_based_tasks(include_examples: bool = True):
    """Get all tasks organized by emotion"""
    try:
        result = recommendation_controller.get_emotion_based_tasks(
            include_examples=include_examples
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/zone/{zone}", tags=["Recommendations"])
async def get_zone_tasks(
    zone: str,
    count: int = Query(5, ge=1, le=20)
):
    """Get tasks for a specific zone"""
    try:
        if zone.upper() not in TASK_ZONES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid zone. Must be one of: {list(TASK_ZONES.keys())}"
            )
        
        result = recommendation_controller.get_zone_recommendations(
            zone=zone,
            count=count
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/dashboard", tags=["Analytics"])
async def get_dashboard_analytics(use_cache: bool = True):
    """Get comprehensive dashboard analytics"""
    try:
        result = analytics_controller.get_dashboard_analytics(use_cache=use_cache)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/emotion", tags=["Analytics"])
async def get_emotion_analytics(
    days: int = Query(30, ge=1, le=365),
    team_id: Optional[str] = None
):
    """Get emotion analytics report"""
    try:
        result = analytics_controller.get_emotion_analytics_report(
            days=days,
            team_id=team_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/stress", tags=["Analytics"])
async def get_stress_analytics(
    days: int = Query(30, ge=1, le=365),
    team_id: Optional[str] = None
):
    """Get stress analytics report"""
    try:
        result = analytics_controller.get_stress_analytics_report(
            days=days,
            team_id=team_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/user/{user_id}", tags=["Analytics"])
async def get_user_activity_report(
    user_id: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get user activity report"""
    try:
        result = analytics_controller.get_user_activity_report(
            user_id=user_id,
            days=days
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/team/{team_id}", tags=["Analytics"])
async def get_team_report(
    team_id: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get comprehensive team report"""
    try:
        result = analytics_controller.get_team_report(
            team_id=team_id,
            days=days
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/trends/emotions", tags=["Analytics"])
async def get_trending_emotions(days: int = Query(7, ge=1, le=90)):
    """Get trending emotions"""
    try:
        result = analytics_controller.get_trending_emotions(days=days)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )