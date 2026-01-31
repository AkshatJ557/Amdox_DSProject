"""
Employee Session Page - Active emotion detection session
"""
import streamlit as st
import time
import random
from datetime import datetime

# Add parent directories to path
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.dirname(current_dir)
components_dir = os.path.dirname(pages_dir)
app_dir = os.path.dirname(components_dir)
root_dir = os.path.dirname(app_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.session import session_manager
from frontend.components.camera import emotion_camera_input, display_emotion_result


def employee_session():
    """Display employee session page"""
    st.set_page_config(
        page_title="Emotion Session - Amdox",
        page_icon="🎥",
        layout="wide"
    )
    
    # Check authentication
    if not session_manager.is_logged_in():
        st.warning("Please log in to start a session")
        st.switch_page("frontend.pages.login")
        return
    
    st.title("🎥 Emotion Detection Session")
    st.markdown(f"Session for **{session_manager.get_user_id()}**")
    
    # Session controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Start Session"):
            session_id = f"session_{int(time.time())}"
            session_manager.start_session(session_id)
            st.session_state.session_id = session_id
            st.session_state.session_active = True
            st.session_state.detection_count = 0
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pause"):
            st.session_state.session_active = False
            st.rerun()
    
    with col3:
        if st.button("▶️ Resume"):
            st.session_state.session_active = True
            st.rerun()
    
    with col4:
        if st.button("⏹️ End Session"):
            session_manager.end_session()
            st.session_state.session_active = False
            st.session_state.session_id = None
            st.rerun()
    
    st.markdown("---")
    
    # Active session display
    if st.session_state.get('session_active', False):
        show_active_session()
    else:
        st.info("Click 'Start Session' to begin emotion detection")


def show_active_session():
    """Show active detection session"""
    st.subheader("🔴 Live Detection")
    
    # Camera input
    img, captured = emotion_camera_input()
    
    if captured:
        # Simulate emotion detection (in real app, this would call the API)
        emotions = ['Happy', 'Neutral', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust']
        detected = random.choice(emotions)
        confidence = random.uniform(0.75, 0.98)
        
        # Update session
        st.session_state.detection_count += 1
        
        # Display result
        display_emotion_result(detected, confidence)
        
        # Update stress score
        stress_mapping = {'Happy': 1, 'Neutral': 4, 'Sad': 6, 'Angry': 8, 'Fear': 7, 'Disgust': 8}
        session_manager.set_stress_score(stress_mapping.get(detected, 5))
        session_manager.set_current_emotion(detected)
    
    # Session stats
    st.markdown("---")
    st.subheader("📊 Session Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Detections", st.session_state.get('detection_count', 0))
    
    with col2:
        current_emotion = session_manager.get_current_emotion()
        st.metric("Current Emotion", current_emotion or "None")
    
    with col3:
        current_stress = session_manager.get_stress_score()
        st.metric("Current Stress", f"{current_stress}/10")
    
    # Live chart placeholder
    st.subheader("📈 Live Emotion Feed")
    st.info("Emotion detection results will appear here in real-time")
    
    # Recent detections
    if st.session_state.get('detection_count', 0) > 0:
        st.markdown("### Recent Detections")
        for i in range(min(st.session_state.get('detection_count', 0), 5)):
            st.write(f"- Detection {i+1}: {random.choice(['Happy', 'Neutral', 'Sad'])} - {random.uniform(0.8, 0.99):.2%}")


if __name__ == "__main__":
    employee_session()

