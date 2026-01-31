"""
Session management for Amdox Frontend
"""
import os
import streamlit as st

# API configuration - use environment variable or default to localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

# API endpoints
API_ENDPOINTS = {
    "health": f"{API_BASE_URL}/health",
    "config": f"{API_BASE_URL}/config",
    "test_backend": f"{API_BASE_URL}/test/backend",
    "emotion_session_start": f"{API_BASE_URL}/emotion/session/start",
    "emotion_session_status": f"{API_BASE_URL}/emotion/session",
    "emotion_complete": f"{API_BASE_URL}/emotion/session",
    "emotion_validate": f"{API_BASE_URL}/emotion/validate",
    "stress_calculate": f"{API_BASE_URL}/stress/calculate",
    "stress_history": f"{API_BASE_URL}/stress/history",
    "stress_trend": f"{API_BASE_URL}/stress/trend",
    "stress_check_threshold": f"{API_BASE_URL}/stress/check-threshold",
    "recommend_task": f"{API_BASE_URL}/recommend/task",
    "recommend_multiple": f"{API_BASE_URL}/recommend/multiple",
    "recommend_tasks_by_emotion": f"{API_BASE_URL}/recommend/tasks-by-emotion",
    "analytics_dashboard": f"{API_BASE_URL}/analytics/dashboard",
    "analytics_emotion": f"{API_BASE_URL}/analytics/emotion",
    "analytics_stress": f"{API_BASE_URL}/analytics/stress",
    "analytics_user": f"{API_BASE_URL}/analytics/user",
    "db_collections": f"{API_BASE_URL}/db/collections",
    "db_health": f"{API_BASE_URL}/db/health"
}


def get_api_url(endpoint_name: str) -> str:
    """
    Get API URL for a given endpoint name
    
    Args:
        endpoint_name: Name of the endpoint
    
    Returns:
        str: Full API URL
    """
    return API_ENDPOINTS.get(endpoint_name, f"{API_BASE_URL}/")


def set_api_url(url: str):
    """
    Set a custom API base URL
    
    Args:
        url: New API base URL
    """
    global API_BASE_URL, API_ENDPOINTS
    API_BASE_URL = url
    # Update all endpoints
    for key in list(API_ENDPOINTS.keys()):
        if key in ["health", "config", "test_backend"]:
            API_ENDPOINTS[key] = f"{url}/{key}"
        elif key.startswith("emotion"):
            API_ENDPOINTS[key] = f"{url}/{key.replace('_', '/', 1)}"
        elif key.startswith("stress"):
            API_ENDPOINTS[key] = f"{url}/{key.replace('_', '/', 1)}"
        elif key.startswith("recommend"):
            API_ENDPOINTS[key] = f"{url}/{key.replace('_', '/', 1)}"
        elif key.startswith("analytics"):
            API_ENDPOINTS[key] = f"{url}/{key.replace('_', '/', 1)}"
        elif key.startswith("db_"):
            API_ENDPOINTS[key] = f"{url}/{key.replace('_', '/')}"


class SessionManager:
    """
    Manages user session state
    """
    
    def __init__(self):
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if "is_authenticated" not in st.session_state:
            st.session_state.is_authenticated = False
        if "current_emotion" not in st.session_state:
            st.session_state.current_emotion = None
        if "stress_score" not in st.session_state:
            st.session_state.stress_score = 0
        if "session_active" not in st.session_state:
            st.session_state.session_active = False
        if "session_id" not in st.session_state:
            st.session_state.session_id = None
    
    def login(self, user_id: str):
        """
        Log in a user
        
        Args:
            user_id: User ID
        """
        st.session_state.user_id = user_id
        st.session_state.is_authenticated = True
    
    def logout(self):
        """Log out the current user"""
        st.session_state.user_id = None
        st.session_state.is_authenticated = False
        st.session_state.current_emotion = None
        st.session_state.stress_score = 0
        st.session_state.session_active = False
        st.session_state.session_id = None
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return st.session_state.is_authenticated
    
    def get_user_id(self) -> str:
        """Get current user ID"""
        return st.session_state.user_id
    
    def set_current_emotion(self, emotion: str):
        """Set current detected emotion"""
        st.session_state.current_emotion = emotion
    
    def get_current_emotion(self) -> str:
        """Get current detected emotion"""
        return st.session_state.current_emotion
    
    def set_stress_score(self, score: int):
        """Set current stress score"""
        st.session_state.stress_score = score
    
    def get_stress_score(self) -> int:
        """Get current stress score"""
        return st.session_state.stress_score
    
    def start_session(self, session_id: str):
        """Start an emotion detection session"""
        st.session_state.session_id = session_id
        st.session_state.session_active = True
    
    def end_session(self):
        """End current emotion detection session"""
        st.session_state.session_id = None
        st.session_state.session_active = False
    
    def is_session_active(self) -> bool:
        """Check if session is active"""
        return st.session_state.session_active
    
    def get_session_id(self) -> str:
        """Get current session ID"""
        return st.session_state.session_id


# Create global session manager instance
session_manager = SessionManager()

