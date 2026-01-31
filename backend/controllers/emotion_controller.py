"""
Enhanced Emotion Detection Controller for Amdox
Production-grade emotion detection with advanced session management and frame processing
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import logging
from collections import deque

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
from backend.database.mood_repo import mood_repo
from backend.ml.emotion.emotion_model import emotion_model
from backend.ml.emotion.dominant_emotion import dominant_emotion_analyzer


class EmotionController:
    """
    Enhanced Controller for emotion detection endpoints
    """
    
    def __init__(self):
        self.model = emotion_model
        self.analyzer = dominant_emotion_analyzer
        self.mood_repo = mood_repo
        self.sessions = {}  # In-memory session storage
        self.session_timeout = 1800  # 30 minutes
        self.max_frame_buffer = 100  # Max frames to buffer per session
        logger.info("✅ Emotion Controller initialized")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions from memory"""
        try:
            now = datetime.utcnow()
            expired = []
            
            for session_id, session in self.sessions.items():
                start_time = session.get("start_time")
                if start_time and (now - start_time).seconds > self.session_timeout:
                    expired.append(session_id)
            
            for session_id in expired:
                del self.sessions[session_id]
                logger.info(f"🗑️ Cleaned up expired session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def start_emotion_session(
        self, 
        user_id: str, 
        session_data: Optional[Dict] = None,
        duration_minutes: int = 20
    ) -> Dict[str, Any]:
        """
        Start a new emotion detection session with enhanced tracking
        
        Args:
            user_id: User ID
            session_data: Optional session metadata
            duration_minutes: Expected session duration
        
        Returns:
            dict: Session information
        """
        try:
            # Cleanup old sessions
            self._cleanup_expired_sessions()
            
            # Validate input
            if not user_id:
                return {
                    "success": False,
                    "error": "user_id is required"
                }
            
            if duration_minutes < 1 or duration_minutes > 120:
                return {
                    "success": False,
                    "error": "duration_minutes must be between 1 and 120"
                }
            
            session_id = str(uuid.uuid4())
            
            session = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.utcnow(),
                "expected_end_time": datetime.utcnow() + timedelta(minutes=duration_minutes),
                "duration_minutes": duration_minutes,
                "status": "active",
                "data": session_data or {},
                "entries": deque(maxlen=self.max_frame_buffer),  # Limit buffer size
                "frame_count": 0,
                "emotion_counts": {},
                "stress_accumulator": []
            }
            
            self.sessions[session_id] = session
            
            logger.info(f"✅ Session started: {session_id} for user: {user_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "start_time": session["start_time"].isoformat(),
                "expected_end_time": session["expected_end_time"].isoformat(),
                "duration_minutes": duration_minutes,
                "status": "active",
                "message": "Session started successfully",
                "instructions": [
                    "Ensure good lighting",
                    "Face the camera directly",
                    "Remove any face coverings",
                    "Stay still during capture"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error starting emotion session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed status of an emotion session
        
        Args:
            session_id: Session ID
        
        Returns:
            dict: Session status with comprehensive metrics
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found or expired"
                }
            
            now = datetime.utcnow()
            elapsed = (now - session["start_time"]).total_seconds() / 60
            remaining = max(0, session["duration_minutes"] - elapsed)
            
            # Calculate progress
            progress_percentage = min(100, (elapsed / session["duration_minutes"]) * 100)
            
            # Get current emotion distribution
            emotion_dist = dict(session.get("emotion_counts", {}))
            
            # Get average stress
            stress_scores = session.get("stress_accumulator", [])
            avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": session["user_id"],
                "status": session["status"],
                "start_time": session["start_time"].isoformat(),
                "expected_end_time": session["expected_end_time"].isoformat(),
                "elapsed_minutes": round(elapsed, 2),
                "remaining_minutes": round(remaining, 2),
                "progress_percentage": round(progress_percentage, 2),
                "metrics": {
                    "frame_count": session["frame_count"],
                    "entry_count": len(session["entries"]),
                    "emotion_distribution": emotion_dist,
                    "average_stress": round(avg_stress, 2),
                    "current_emotion": session.get("last_emotion"),
                    "current_confidence": session.get("last_confidence")
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting session status: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def pause_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Pause an active emotion session
        
        Args:
            session_id: Session ID
            user_id: User ID
        
        Returns:
            dict: Pause status
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            if session["user_id"] != user_id:
                return {
                    "success": False,
                    "error": "User ID mismatch"
                }
            
            if session["status"] != "active":
                return {
                    "success": False,
                    "error": f"Session is {session['status']}, cannot pause"
                }
            
            session["status"] = "paused"
            session["paused_at"] = datetime.utcnow()
            
            logger.info(f"⏸️ Session paused: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "status": "paused",
                "message": "Session paused successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error pausing session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def resume_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Resume a paused emotion session
        
        Args:
            session_id: Session ID
            user_id: User ID
        
        Returns:
            dict: Resume status
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            if session["user_id"] != user_id:
                return {
                    "success": False,
                    "error": "User ID mismatch"
                }
            
            if session["status"] != "paused":
                return {
                    "success": False,
                    "error": f"Session is {session['status']}, cannot resume"
                }
            
            # Adjust expected end time based on pause duration
            if "paused_at" in session:
                pause_duration = (datetime.utcnow() - session["paused_at"]).total_seconds() / 60
                session["expected_end_time"] += timedelta(minutes=pause_duration)
                del session["paused_at"]
            
            session["status"] = "active"
            
            logger.info(f"▶️ Session resumed: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "status": "active",
                "message": "Session resumed successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error resuming session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_session(
        self, 
        session_id: str, 
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Complete an emotion session with comprehensive analysis
        
        Args:
            session_id: Session ID
            user_id: User ID
            context: Optional context data
            save_to_db: Whether to save results to database
        
        Returns:
            dict: Session completion results with analytics
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            if session["user_id"] != user_id:
                return {
                    "success": False,
                    "error": "User ID mismatch"
                }
            
            # Mark session as complete
            session["status"] = "completed"
            session["end_time"] = datetime.utcnow()
            session["context"] = context or {}
            
            # Calculate session summary
            entries = list(session["entries"])
            
            if entries:
                from collections import Counter
                
                # Get emotion distribution
                emotions = [e.get("dominant_emotion", "Unknown") for e in entries]
                emotion_counter = Counter(emotions)
                
                # Get stress statistics
                stress_scores = [e.get("stress_score", 0) for e in entries]
                avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
                max_stress = max(stress_scores) if stress_scores else 0
                min_stress = min(stress_scores) if stress_scores else 0
                
                # Determine dominant emotion (most common)
                dominant_emotion = emotion_counter.most_common(1)[0][0]
                
                # Calculate confidence statistics
                confidences = [e.get("confidence", 0) for e in entries]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Calculate session quality score
                quality_score = self._calculate_session_quality(
                    len(entries),
                    avg_confidence,
                    session["duration_minutes"]
                )
                
                result = {
                    "success": True,
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": "completed",
                    "timing": {
                        "start_time": session["start_time"].isoformat(),
                        "end_time": session["end_time"].isoformat(),
                        "duration_minutes": (
                            session["end_time"] - session["start_time"]
                        ).total_seconds() / 60,
                        "expected_duration": session["duration_minutes"]
                    },
                    "metrics": {
                        "total_frames": session["frame_count"],
                        "valid_entries": len(entries),
                        "quality_score": quality_score
                    },
                    "emotion_analysis": {
                        "dominant_emotion": dominant_emotion,
                        "distribution": dict(emotion_counter),
                        "average_confidence": round(avg_confidence, 3)
                    },
                    "stress_analysis": {
                        "average_stress": round(avg_stress, 2),
                        "max_stress": max_stress,
                        "min_stress": min_stress,
                        "stress_level": self._get_stress_level(avg_stress)
                    },
                    "context": context or {},
                    "recommendations": self._generate_session_recommendations(
                        dominant_emotion,
                        avg_stress,
                        quality_score
                    )
                }
                
                # Save to database if requested
                if save_to_db:
                    db_result = self._save_session_to_db(session, result)
                    result["saved_to_db"] = db_result
                
            else:
                result = {
                    "success": True,
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": "completed",
                    "message": "Session completed with no emotion entries",
                    "entry_count": 0,
                    "warning": "No frames were processed during this session"
                }
            
            # Clean up session from memory
            del self.sessions[session_id]
            
            logger.info(f"✅ Session completed: {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error completing session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_session_quality(
        self, 
        entry_count: int, 
        avg_confidence: float,
        duration_minutes: int
    ) -> int:
        """Calculate session quality score (0-100)"""
        try:
            score = 0
            
            # Entry count score (max 40 points)
            expected_entries = duration_minutes * 3  # Expect 3 entries per minute
            entry_score = min(40, (entry_count / expected_entries) * 40)
            score += entry_score
            
            # Confidence score (max 40 points)
            confidence_score = avg_confidence * 40
            score += confidence_score
            
            # Consistency score (max 20 points)
            if entry_count >= expected_entries * 0.8:
                score += 20
            elif entry_count >= expected_entries * 0.5:
                score += 10
            
            return int(min(100, score))
            
        except Exception:
            return 50  # Default score
    
    def _get_stress_level(self, score: float) -> str:
        """Get stress level label"""
        if score >= 8:
            return "Very High"
        elif score >= 6:
            return "High"
        elif score >= 4:
            return "Moderate"
        else:
            return "Low"
    
    def _generate_session_recommendations(
        self,
        dominant_emotion: str,
        avg_stress: float,
        quality_score: int
    ) -> List[str]:
        """Generate recommendations based on session results"""
        recommendations = []
        
        try:
            # Quality-based recommendations
            if quality_score < 50:
                recommendations.append("💡 Try to complete more detections for better insights")
            
            # Emotion-based recommendations
            if dominant_emotion in ['Sad', 'Angry', 'Fear']:
                recommendations.append(f"🧘 Your dominant emotion ({dominant_emotion}) suggests taking a break")
            elif dominant_emotion == 'Happy':
                recommendations.append("🌟 Great session! You're in a positive state")
            
            # Stress-based recommendations
            if avg_stress >= 7:
                recommendations.append("🚨 High stress detected - consider stress relief activities")
            elif avg_stress >= 5:
                recommendations.append("⚠️ Moderate stress - take regular breaks")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations if recommendations else ["Session completed successfully"]
    
    def _save_session_to_db(self, session: Dict, result: Dict) -> bool:
        """Save session results to database"""
        try:
            # Create mood entry for the session
            mood_entry = {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "timestamp": session["end_time"],
                "dominant_emotion": result["emotion_analysis"]["dominant_emotion"],
                "confidence": result["emotion_analysis"]["average_confidence"],
                "stress_score": int(result["stress_analysis"]["average_stress"]),
                "emotions": result["emotion_analysis"]["distribution"],
                "duration_minutes": result["timing"]["duration_minutes"],
                "quality_score": result["metrics"]["quality_score"],
                "session_metadata": {
                    "total_frames": result["metrics"]["total_frames"],
                    "valid_entries": result["metrics"]["valid_entries"],
                    "context": result.get("context", {})
                }
            }
            
            self.mood_repo.save_mood_entry(mood_entry)
            logger.info(f"💾 Session saved to database: {session['session_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session to database: {e}")
            return False
    
    def validate_camera(self) -> Dict[str, Any]:
        """
        Validate camera and emotion model availability with detailed diagnostics
        
        Returns:
            dict: Validation results
        """
        try:
            # Check if model is loaded
            model_loaded = self.model.loaded if self.model else False
            
            # Get model info
            model_info = self.model.get_model_info() if self.model else {}
            
            # Try a simple camera check
            camera_available = False
            camera_error = None
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    camera_available = True
                    # Try to read a frame
                    ret, frame = cap.read()
                    if not ret:
                        camera_error = "Camera opened but cannot read frames"
                cap.release()
            except Exception as e:
                camera_error = str(e)
            
            # Overall system status
            system_ready = model_loaded and camera_available
            
            return {
                "success": True,
                "system_ready": system_ready,
                "camera": {
                    "available": camera_available,
                    "status": "available" if camera_available else "not_available",
                    "error": camera_error
                },
                "emotion_model": {
                    "loaded": model_loaded,
                    "model_path": self.model.model_path if self.model else None,
                    "emotion_labels": self.model.EMOTION_LABELS if self.model else [],
                    "input_shape": model_info.get("input_shape"),
                    "output_shape": model_info.get("output_shape")
                },
                "recommendations": self._get_system_recommendations(
                    model_loaded, 
                    camera_available
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Error validating camera: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "camera": {"available": False, "status": "error"},
                "emotion_model": {"loaded": False}
            }
    
    def _get_system_recommendations(
        self, 
        model_loaded: bool, 
        camera_available: bool
    ) -> List[str]:
        """Get system setup recommendations"""
        recommendations = []
        
        if not model_loaded:
            recommendations.append("⚠️ Emotion model not loaded - check model file path")
        
        if not camera_available:
            recommendations.append("⚠️ Camera not available - check camera permissions")
            recommendations.append("💡 Ensure no other application is using the camera")
        
        if model_loaded and camera_available:
            recommendations.append("✅ System is ready for emotion detection")
        
        return recommendations
    
    def process_frame(
        self, 
        session_id: str, 
        frame_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a video frame and detect emotion with enhanced tracking
        
        Args:
            session_id: Session ID
            frame_data: Frame data (base64 or image bytes)
        
        Returns:
            dict: Emotion detection result
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Invalid or expired session"
                }
            
            if session["status"] != "active":
                return {
                    "success": False,
                    "error": f"Session is {session['status']}, not active"
                }
            
            # Increment frame counter
            session["frame_count"] += 1
            
            # Detect emotion
            result = self.analyzer.analyze_frame(frame_data)
            
            if result["success"]:
                # Add timestamp
                result["timestamp"] = datetime.utcnow().isoformat()
                
                # Add to session entries
                entry = {
                    "timestamp": datetime.utcnow(),
                    "dominant_emotion": result["dominant_emotion"],
                    "confidence": result["confidence"],
                    "emotions": result["emotions"],
                    "stress_score": result.get("stress_score", 0)
                }
                session["entries"].append(entry)
                
                # Update emotion counts
                emotion = result["dominant_emotion"]
                session["emotion_counts"][emotion] = session["emotion_counts"].get(emotion, 0) + 1
                
                # Update stress accumulator
                session["stress_accumulator"].append(result.get("stress_score", 0))
                
                # Update last detected values
                session["last_emotion"] = emotion
                session["last_confidence"] = result["confidence"]
                
                # Save individual entry to database
                mood_entry = {
                    "session_id": session_id,
                    "user_id": session["user_id"],
                    "timestamp": datetime.utcnow(),
                    "dominant_emotion": result["dominant_emotion"],
                    "confidence": result["confidence"],
                    "emotions": result["emotions"],
                    "stress_score": result.get("stress_score", 0)
                }
                self.mood_repo.save_mood_entry(mood_entry)
                
                logger.debug(f"📸 Frame processed for session {session_id}: {emotion}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing frame: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get real-time statistics for an active session
        
        Args:
            session_id: Session ID
        
        Returns:
            dict: Session statistics
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            entries = list(session["entries"])
            
            if not entries:
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "No entries yet",
                    "statistics": {}
                }
            
            from collections import Counter
            
            # Calculate statistics
            emotions = [e["dominant_emotion"] for e in entries]
            emotion_counter = Counter(emotions)
            
            stress_scores = [e["stress_score"] for e in entries]
            confidences = [e["confidence"] for e in entries]
            
            return {
                "success": True,
                "session_id": session_id,
                "statistics": {
                    "total_detections": len(entries),
                    "emotion_distribution": dict(emotion_counter),
                    "most_common_emotion": emotion_counter.most_common(1)[0][0],
                    "average_stress": round(sum(stress_scores) / len(stress_scores), 2),
                    "max_stress": max(stress_scores),
                    "min_stress": min(stress_scores),
                    "average_confidence": round(sum(confidences) / len(confidences), 3),
                    "recent_emotions": [e["dominant_emotion"] for e in list(entries)[-5:]]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting session statistics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Create global controller instance
emotion_controller = EmotionController()