"""
Enhanced Camera Component for Amdox
Real-time emotion detection with webcam integration
"""
import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import base64
import requests
from typing import Optional, Dict, Any
import time

# API Configuration
API_BASE_URL = "http://localhost:8080"


class CameraComponent:
    """
    Enhanced camera component for emotion detection
    """
    
    def __init__(self):
        self.camera = None
        self.is_active = False
        
    def initialize_camera(self) -> bool:
        """
        Initialize webcam
        
        Returns:
            bool: True if successful
        """
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                st.error("❌ Could not open camera")
                return False
            
            # Set camera properties for better quality
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_active = True
            return True
            
        except Exception as e:
            st.error(f"❌ Camera initialization error: {e}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera
        
        Returns:
            np.ndarray: Captured frame or None
        """
        if not self.is_active or self.camera is None:
            return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                return frame
            return None
            
        except Exception as e:
            st.error(f"❌ Frame capture error: {e}")
            return None
    
    def release_camera(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.is_active = False
    
    def encode_frame_base64(self, frame: np.ndarray) -> str:
        """
        Encode frame to base64 for API transmission
        
        Args:
            frame: Image frame
        
        Returns:
            str: Base64 encoded image
        """
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            return frame_base64
        except Exception as e:
            st.error(f"❌ Frame encoding error: {e}")
            return ""


def validate_camera_setup():
    """
    Validate camera and model setup
    
    Returns:
        dict: Validation results
    """
    try:
        response = requests.get(f"{API_BASE_URL}/emotion/validate_camera", timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": "Could not validate camera"
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"API connection error: {e}"
        }


def render_camera_preview():
    """
    Render camera preview with controls
    """
    st.markdown("### 📸 Camera Preview")
    
    # Initialize session state
    if 'camera_component' not in st.session_state:
        st.session_state.camera_component = CameraComponent()
    
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    
    camera_comp = st.session_state.camera_component
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🎥 Start Camera", disabled=st.session_state.camera_active):
            if camera_comp.initialize_camera():
                st.session_state.camera_active = True
                st.success("✅ Camera started")
                st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Camera", disabled=not st.session_state.camera_active):
            camera_comp.release_camera()
            st.session_state.camera_active = False
            st.info("Camera stopped")
            st.rerun()
    
    with col3:
        if st.button("🔍 Validate Setup"):
            with st.spinner("Validating..."):
                result = validate_camera_setup()
                
                if result.get("success"):
                    st.success("✅ Camera and model ready")
                    
                    if result.get("camera_available"):
                        st.info("📷 Camera: Available")
                    if result.get("model_loaded"):
                        st.info("🧠 Model: Loaded")
                else:
                    st.error(f"❌ {result.get('error', 'Validation failed')}")
    
    # Display camera feed
    if st.session_state.camera_active:
        st.markdown("---")
        
        # Create placeholder for video feed
        frame_placeholder = st.empty()
        
        # Capture and display frame
        frame = camera_comp.capture_frame()
        
        if frame is not None:
            # Convert BGR to RGB for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Display frame
            frame_placeholder.image(
                frame_rgb,
                caption="Live Camera Feed",
                use_column_width=True
            )
        else:
            st.warning("⚠️ No frame available")


def render_session_controls(user_id: str):
    """
    Render emotion detection session controls
    
    Args:
        user_id: Current user ID
    """
    st.markdown("### 🎬 Detection Session")
    
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    
    if 'session_active' not in st.session_state:
        st.session_state.session_active = False
    
    if 'detection_count' not in st.session_state:
        st.session_state.detection_count = 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        duration = st.number_input(
            "Session Duration (minutes)",
            min_value=1,
            max_value=60,
            value=20,
            disabled=st.session_state.session_active
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not st.session_state.session_active:
            if st.button("▶️ Start Detection Session", use_container_width=True):
                # Start session via API
                with st.spinner("Starting session..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/emotion/session/start",
                            json={
                                "user_id": user_id,
                                "duration_minutes": duration
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            if result.get("success"):
                                st.session_state.session_id = result.get("session_id")
                                st.session_state.session_active = True
                                st.session_state.detection_count = 0
                                st.success(f"✅ Session started: {result.get('session_id')}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error')}")
                        else:
                            st.error(f"❌ API error: {response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Connection error: {e}")
        else:
            if st.button("⏹️ End Session", use_container_width=True):
                # Complete session via API
                with st.spinner("Completing session..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/emotion/session/complete",
                            json={
                                "session_id": st.session_state.session_id,
                                "user_id": user_id,
                                "save_to_db": True
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            if result.get("success"):
                                st.success("✅ Session completed!")
                                
                                # Display summary
                                summary = result.get("summary", {})
                                st.info(f"📊 Total detections: {summary.get('total_detections', 0)}")
                                st.info(f"😊 Dominant emotion: {summary.get('dominant_emotion', 'N/A')}")
                                st.info(f"📈 Avg stress: {summary.get('average_stress', 0)}/10")
                                
                                # Reset session
                                st.session_state.session_id = None
                                st.session_state.session_active = False
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error')}")
                        else:
                            st.error(f"❌ API error: {response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Connection error: {e}")
    
    # Session status
    if st.session_state.session_active:
        st.markdown("---")
        
        # Get session status
        try:
            response = requests.get(
                f"{API_BASE_URL}/emotion/session/{st.session_state.session_id}/status",
                timeout=5
            )
            
            if response.status_code == 200:
                status = response.json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", status.get("status", "Unknown"))
                
                with col2:
                    elapsed = status.get("elapsed_minutes", 0)
                    st.metric("Elapsed", f"{elapsed:.1f} min")
                
                with col3:
                    remaining = status.get("remaining_minutes", 0)
                    st.metric("Remaining", f"{remaining:.1f} min")
                
                # Progress bar
                progress = status.get("progress_percentage", 0) / 100
                st.progress(progress)
                
        except Exception as e:
            st.warning(f"⚠️ Could not fetch status: {e}")


def render_live_detection(user_id: str):
    """
    Render live emotion detection with camera feed
    
    Args:
        user_id: Current user ID
    """
    st.markdown("### 🔴 Live Detection")
    
    if not st.session_state.get('session_active'):
        st.info("ℹ️ Start a detection session to begin")
        return
    
    if not st.session_state.get('camera_active'):
        st.warning("⚠️ Please start the camera first")
        return
    
    # Capture frame
    camera_comp = st.session_state.camera_component
    frame = camera_comp.capture_frame()
    
    if frame is not None:
        # Encode frame
        frame_base64 = camera_comp.encode_frame_base64(frame)
        
        # Send to API for detection
        try:
            response = requests.post(
                f"{API_BASE_URL}/emotion/process_frame",
                json={
                    "session_id": st.session_state.session_id,
                    "frame_base64": frame_base64
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.session_state.detection_count += 1
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        emotion = result.get("dominant_emotion", "Unknown")
                        st.metric("Emotion", emotion)
                    
                    with col2:
                        confidence = result.get("confidence", 0)
                        st.metric("Confidence", f"{confidence:.1%}")
                    
                    with col3:
                        stress = result.get("stress_score", 0)
                        st.metric("Stress", f"{stress}/10")
                    
                    # Detection count
                    st.caption(f"Total detections: {st.session_state.detection_count}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Detection error: {e}")
    else:
        st.warning("⚠️ No frame available")


def render_camera_page(user_id: str):
    """
    Render complete camera page
    
    Args:
        user_id: Current user ID
    """
    st.title("📷 Emotion Detection Camera")
    
    # Camera preview
    render_camera_preview()
    
    st.markdown("---")
    
    # Session controls
    render_session_controls(user_id)
    
    st.markdown("---")
    
    # Live detection (auto-refresh)
    if st.session_state.get('session_active') and st.session_state.get('camera_active'):
        # Auto-refresh every 2 seconds
        if st.button("🔄 Detect Emotion"):
            render_live_detection(user_id)
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (every 3 seconds)", value=False)
        
        if auto_refresh:
            time.sleep(3)
            st.rerun()


# Helper function for cleanup
def cleanup_camera():
    """Cleanup camera resources on page exit"""
    if 'camera_component' in st.session_state:
        st.session_state.camera_component.release_camera()


if __name__ == "__main__":
    # For testing
    render_camera_page("test_user_001")