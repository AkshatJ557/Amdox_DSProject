"""
Employee Session Page for Amdox
Real-time emotion detection session management
"""
import streamlit as st
import requests
from datetime import datetime
import time
import sys
import os

# Add components to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'components'))

from navbar import render_navbar, render_sidebar_navigation, render_page_header, render_status_bar
from components.camera import (
    CameraComponent,
    render_camera_preview,
    render_session_controls,
    render_live_detection,
    validate_camera_setup
)
from components.charts import create_stress_gauge, create_emotion_pie_chart
from components.forms import render_stress_context_form

# API Configuration
API_BASE_URL = "http://localhost:8080"


def render_session_dashboard(session_id: str):
    """
    Render real-time session dashboard
    
    Args:
        session_id: Active session ID
    """
    st.markdown("### 📊 Session Dashboard")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/emotion/session/{session_id}/statistics",
            timeout=5
        )
        
        if response.status_code == 200:
            stats = response.json()
            
            if stats.get('success'):
                data = stats.get('statistics', {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Detections",
                        data.get('total_detections', 0)
                    )
                
                with col2:
                    dominant = data.get('dominant_emotion', 'Unknown')
                    st.metric(
                        "Dominant Emotion",
                        dominant
                    )
                
                with col3:
                    avg_stress = data.get('avg_stress', 0)
                    st.metric(
                        "Avg Stress",
                        f"{avg_stress:.1f}/10"
                    )
                
                with col4:
                    avg_confidence = data.get('avg_confidence', 0)
                    st.metric(
                        "Avg Confidence",
                        f"{avg_confidence:.1%}"
                    )
                
                # Emotion distribution
                emotion_dist = data.get('emotion_distribution', {})
                if emotion_dist:
                    st.plotly_chart(
                        create_emotion_pie_chart(emotion_dist),
                        use_container_width=True,
                        key="session_emotion_dist"
                    )
    except Exception as e:
        st.warning(f"Could not load session statistics: {e}")


def render_detection_history(session_id: str):
    """
    Render detection history for current session
    
    Args:
        session_id: Session ID
    """
    st.markdown("### 📜 Detection History")
    
    if 'detection_history' not in st.session_state:
        st.session_state.detection_history = []
    
    history = st.session_state.detection_history
    
    if history:
        # Show last 10 detections
        for idx, detection in enumerate(reversed(history[-10:]), 1):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            
            with col1:
                st.caption(f"#{idx}")
            
            with col2:
                emotion = detection.get('emotion', 'Unknown')
                st.caption(f"😊 {emotion}")
            
            with col3:
                stress = detection.get('stress', 0)
                st.caption(f"💊 Stress: {stress}/10")
            
            with col4:
                timestamp = detection.get('timestamp', '')
                st.caption(timestamp[-8:] if timestamp else '')
    else:
        st.info("No detections yet")


def render_employee_session():
    """Main employee session page"""
    
    # Check login
    if 'user_id' not in st.session_state:
        st.warning("⚠️ Please login first")
        if st.button("🔐 Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return
    
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name', 'Employee')
    
    # Navbar
    render_navbar(user_id, user_name)
    
    # Sidebar
    selected_page = render_sidebar_navigation()
    if selected_page != "detection":
        st.session_state.page = selected_page
        st.rerun()
    
    # Page header
    render_page_header(
        "Emotion Detection Session",
        "Real-time emotion and stress monitoring",
        "🎥"
    )
    
    # Status bar
    render_status_bar()
    
    st.markdown("---")
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Camera preview
        render_camera_preview()
        
        st.markdown("---")
        
        # Session controls
        render_session_controls(user_id)
    
    with col2:
        # Stress context form
        context = render_stress_context_form()
        
        if context:
            st.session_state.stress_context = context
    
    st.markdown("---")
    
    # Session dashboard (only if session active)
    if st.session_state.get('session_active'):
        session_id = st.session_state.get('session_id')
        
        tab1, tab2 = st.tabs(["📊 Dashboard", "📜 History"])
        
        with tab1:
            render_session_dashboard(session_id)
        
        with tab2:
            render_detection_history(session_id)
        
        st.markdown("---")
        
        # Live detection button
        if st.session_state.get('camera_active'):
            if st.button("🔴 Detect Emotion Now", type="primary", use_container_width=True):
                render_live_detection(user_id)
                
                # Add to history
                if 'detection_history' not in st.session_state:
                    st.session_state.detection_history = []
                
                st.session_state.detection_history.append({
                    'emotion': 'Detected',  # Would be actual detection
                    'stress': 5,  # Would be actual stress
                    'timestamp': datetime.now().isoformat()
                })
    
    # Auto-refresh
    if st.session_state.get('session_active') and st.session_state.get('camera_active'):
        auto_refresh = st.checkbox("🔄 Auto-refresh (every 5 seconds)", value=False)
        
        if auto_refresh:
            time.sleep(5)
            st.rerun()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Detection Session - Amdox",
        page_icon="🎥",
        layout="wide"
    )
    render_employee_session()