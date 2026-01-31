"""
Employee Dashboard - Main dashboard for employees
"""
import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Add parent directories to path
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.dirname(current_dir)
components_dir = os.path.dirname(pages_dir)
app_dir = os.path.dirname(components_dir)
root_dir = os.path.dirname(app_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from frontend.session import session_manager, API_BASE_URL
from frontend.components.camera import emotion_camera_input
from frontend.components.charts import (
    display_emotion_chart, 
    display_stress_chart,
    display_recommendation_card
)
from frontend.components.navbar import show_navbar
from frontend.components.forms import stress_input_form, recommendation_request_form


def employee_dashboard():
    """Display employee dashboard"""
    st.set_page_config(
        page_title="Employee Dashboard - Amdox",
        page_icon="📊",
        layout="wide"
    )
    
    # Check authentication
    if not session_manager.is_logged_in():
        st.warning("Please log in to access the dashboard")
        st.switch_page("frontend.pages.login")
        return
    
    # Show navigation
    show_navbar("Employee Dashboard")
    
    # Main content
    st.title("📊 Employee Dashboard")
    st.markdown(f"Welcome back, **{session_manager.get_user_id()}**!")
    
    # Quick actions
    with st.expander("🎯 Quick Actions", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📸 Detect Emotion"):
                st.session_state.show_camera = True
        
        with col2:
            if st.button("📈 View History"):
                st.session_state.show_history = True
        
        with col3:
            if st.button("💡 Get Recommendation"):
                st.session_state.show_recommendation = True
        
        with col4:
            if st.button("📊 Analytics"):
                st.session_state.show_analytics = True
    
    # Show camera if requested
    if st.session_state.get('show_camera', False):
        show_emotion_detection()
    
    # Show history if requested
    if st.session_state.get('show_history', False):
        show_emotion_history()
    
    # Show recommendation if requested
    if st.session_state.get('show_recommendation', False):
        show_recommendations()
    
    # Show analytics if requested
    if st.session_state.get('show_analytics', False):
        show_analytics()
    
    # Default dashboard view
    if not any([st.session_state.get(x, False) for x in ['show_camera', 'show_history', 'show_recommendation', 'show_analytics']]):
        show_dashboard_overview()


def show_dashboard_overview():
    """Show dashboard overview"""
    # Get current emotion and stress
    current_emotion = session_manager.get_current_emotion()
    current_stress = session_manager.get_stress_score()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Current Emotion",
            value=current_emotion or "Not detected",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Stress Score",
            value=f"{current_stress}/10",
            delta=None
        )
    
    with col3:
        if st.button("📸 New Detection"):
            st.session_state.show_camera = True
            st.rerun()
    
    with col4:
        if st.button("💡 Get Recommendation"):
            if current_emotion:
                st.session_state.show_recommendation = True
            else:
                st.warning("Please detect your emotion first")
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Recent Emotions")
        # Placeholder for chart
        st.info("Start an emotion detection session to see your emotional trends")
    
    with col2:
        st.subheader("💡 Quick Tips")
        st.info("""
        - Take regular breaks to maintain emotional well-being
        - Stay hydrated and get enough sleep
        - Practice mindfulness exercises
        """)


def show_emotion_detection():
    """Show emotion detection interface"""
    st.markdown("---")
    st.subheader("📸 Emotion Detection")
    
    # Camera input
    img, captured = emotion_camera_input()
    
    if captured:
        st.success("Image captured! Analyzing emotion...")
        
        # Process image (in a real app, this would call the API)
        # For demo, simulate detection
        import random
        emotions = ['Happy', 'Neutral', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust']
        detected_emotion = random.choice(emotions)
        confidence = random.uniform(0.7, 0.99)
        
        # Update session
        session_manager.set_current_emotion(detected_emotion)
        
        # Calculate stress score
        stress_mapping = {'Happy': 1, 'Neutral': 4, 'Sad': 6, 'Angry': 8, 'Fear': 7, 'Disgust': 8}
        stress_score = stress_mapping.get(detected_emotion, 5)
        session_manager.set_stress_score(stress_score)
        
        # Display result
        st.success(f"Detected: {detected_emotion} (Confidence: {confidence:.2%})")
        st.progress(int(confidence * 100))
        
        # Ask for stress self-assessment
        st.markdown("### Self-Assessment")
        user_stress = st.slider("Rate your current stress level (1-10)", 1, 10, stress_score)
        
        if st.button("💡 Get Recommendation Based on This"):
            st.session_state.show_recommendation = True
            st.rerun()
    
    if st.button("Back to Dashboard"):
        st.session_state.show_camera = False
        st.rerun()


def show_emotion_history():
    """Show emotion history"""
    st.markdown("---")
    st.subheader("📈 Emotion History")
    
    # Placeholder for history data
    st.info("Your emotion detection history will appear here")
    
    # In a real app, this would fetch from the API
    # try:
    #     response = requests.get(f"{API_BASE_URL}/stress/history/{session_manager.get_user_id()}")
    #     if response.status_code == 200:
    #         data = response.json()
    #         # Display history
    # except Exception as e:
    #     st.error(f"Error fetching history: {e}")
    
    if st.button("Back to Dashboard"):
        st.session_state.show_history = False
        st.rerun()


def show_recommendations():
    """Show recommendations based on emotion"""
    st.markdown("---")
    st.subheader("💡 Personalized Recommendations")
    
    current_emotion = session_manager.get_current_emotion()
    
    if not current_emotion:
        st.warning("No emotion detected yet. Please detect your emotion first.")
        if st.button("Go to Emotion Detection"):
            st.session_state.show_camera = True
            st.session_state.show_recommendation = False
            st.rerun()
        return
    
    # Get recommendation (in real app, call API)
    recommendation = {
        "task": "Take a short break and practice deep breathing",
        "category": "Wellness",
        "priority": "Medium",
        "duration": "10-15 minutes"
    }
    
    display_recommendation_card(recommendation)
    
    # Show related recommendations
    st.markdown("### More Suggestions")
    suggestions = [
        "Practice the 4-7-8 breathing technique",
        "Take a brief walk outside",
        "Listen to calming music",
        "Do a quick meditation session"
    ]
    
    for i, suggestion in enumerate(suggestions):
        st.write(f"{i+1}. {suggestion}")
    
    if st.button("Back to Dashboard"):
        st.session_state.show_recommendation = False
        st.rerun()


def show_analytics():
    """Show analytics dashboard"""
    st.markdown("---")
    st.subheader("📊 Analytics Dashboard")
    
    # Placeholder for analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Emotion Distribution")
        st.info("Analytics data will appear here after multiple detections")
    
    with col2:
        st.markdown("### Stress Trends")
        st.info("Track your stress over time")
    
    if st.button("Back to Dashboard"):
        st.session_state.show_analytics = False
        st.rerun()


if __name__ == "__main__":
    employee_dashboard()

