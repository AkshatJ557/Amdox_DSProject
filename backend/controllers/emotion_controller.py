"""
Emotion detection controller
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

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
    Controller for emotion detection endpoints
    """
    
    def __init__(self):
        self.model = emotion_model
        self.analyzer = dominant_emotion_analyzer
        self.mood_repo = mood_repo
        self.sessions = {}  # In-memory session storage
    
    def start_emotion_session(
        self, 
        user_id: str, 
        session_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Start a new emotion detection session
        
        Args:
            user_id: User ID
            session_data: Optional session metadata
        
        Returns:
            dict: Session information
        """
        try:
            session_id = str(uuid.uuid4())
            
            session = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.utcnow(),
                "status": "active",
                "data": session_data or {},
                "entries": []
            }
            
            self.sessions[session_id] = session
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "start_time": session["start_time"].isoformat(),
                "status": "active",
                "message": "Session started successfully"
            }
            
        except Exception as e:
            print(f"❌ Error starting emotion session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get status of an emotion session
        
        Args:
            session_id: Session ID
        
        Returns:
            dict: Session status
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": session["user_id"],
                "status": session["status"],
                "start_time": session["start_time"].isoformat(),
                "entry_count": len(session["entries"]),
                "duration_minutes": (
                    datetime.utcnow() - session["start_time"]
                ).total_seconds() / 60
            }
            
        except Exception as e:
            print(f"❌ Error getting session status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_session(
        self, 
        session_id: str, 
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete an emotion session and return results
        
        Args:
            session_id: Session ID
            user_id: User ID
            context: Optional context data
        
        Returns:
            dict: Session completion results
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
            entries = session["entries"]
            
            if entries:
                from collections import Counter
                emotion_counter = Counter(e.get("dominant_emotion", "Unknown") for e in entries)
                
                stress_scores = [e.get("stress_score", 0) for e in entries]
                avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
                
                result = {
                    "success": True,
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": "completed",
                    "start_time": session["start_time"].isoformat(),
                    "end_time": session["end_time"].isoformat(),
                    "duration_minutes": (
                        session["end_time"] - session["start_time"]
                    ).total_seconds() / 60,
                    "entry_count": len(entries),
                    "emotion_distribution": dict(emotion_counter),
                    "dominant_emotion": emotion_counter.most_common(1)[0][0],
                    "average_stress": round(avg_stress, 2),
                    "context": context or {}
                }
            else:
                result = {
                    "success": True,
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": "completed",
                    "message": "Session completed with no emotion entries",
                    "entry_count": 0
                }
            
            # Clean up session
            del self.sessions[session_id]
            
            return result
            
        except Exception as e:
            print(f"❌ Error completing session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_camera(self) -> Dict[str, Any]:
        """
        Validate camera and emotion model availability
        
        Returns:
            dict: Validation results
        """
        try:
            # Check if model is loaded
            model_loaded = self.model.loaded if self.model else False
            
            # Try a simple camera check
            camera_available = False
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    camera_available = True
                    cap.release()
            except:
                pass
            
            return {
                "success": True,
                "camera": {
                    "available": camera_available,
                    "status": "available" if camera_available else "not_available"
                },
                "emotion_model": {
                    "loaded": model_loaded,
                    "model_path": self.model.model_path if self.model else None
                }
            }
            
        except Exception as e:
            print(f"❌ Error validating camera: {e}")
            return {
                "success": False,
                "error": str(e),
                "camera": {"available": False, "status": "error"},
                "emotion_model": {"loaded": False}
            }
    
    def process_frame(
        self, 
        session_id: str, 
        frame_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a video frame and detect emotion
        
        Args:
            session_id: Session ID
            frame_data: Frame data (base64 or image bytes)
        
        Returns:
            dict: Emotion detection result
        """
        try:
            session = self.sessions.get(session_id)
            
            if not session or session["status"] != "active":
                return {
                    "success": False,
                    "error": "Invalid or inactive session"
                }
            
            # Detect emotion
            result = self.analyzer.analyze_frame(frame_data)
            
            if result["success"]:
                # Add to session entries
                entry = {
                    "timestamp": datetime.utcnow(),
                    "dominant_emotion": result["dominant_emotion"],
                    "confidence": result["confidence"],
                    "emotions": result["emotions"],
                    "stress_score": result.get("stress_score", 0)
                }
                session["entries"].append(entry)
                
                # Also save to database
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
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing frame: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Create global controller instance
emotion_controller = EmotionController()

