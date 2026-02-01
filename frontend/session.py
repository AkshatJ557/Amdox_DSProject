"""
Enhanced Session Management for Amdox Frontend
Improved API endpoint handling and session state management
"""
import os
import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime

# API configuration - use environment variable or default to localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")


class APIEndpoints:
    """
    Centralized API endpoint management
    Matches endpoints from backend/api.py
    """
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
    
    # ============================================================================
    # HEALTH & STATUS
    # ============================================================================
    
    @property
    def health(self) -> str:
        return f"{self.base_url}/health"
    
    @property
    def db_status(self) -> str:
        return f"{self.base_url}/db/status"
    
    # ============================================================================
    # EMOTION DETECTION
    # ============================================================================
    
    @property
    def emotion_session_start(self) -> str:
        return f"{self.base_url}/emotion/session/start"
    
    def emotion_session_status(self, session_id: str) -> str:
        return f"{self.base_url}/emotion/session/{session_id}/status"
    
    def emotion_session_pause(self, session_id: str) -> str:
        return f"{self.base_url}/emotion/session/{session_id}/pause"
    
    def emotion_session_resume(self, session_id: str) -> str:
        return f"{self.base_url}/emotion/session/{session_id}/resume"
    
    @property
    def emotion_session_complete(self) -> str:
        return f"{self.base_url}/emotion/session/complete"
    
    @property
    def emotion_validate_camera(self) -> str:
        return f"{self.base_url}/emotion/validate_camera"
    
    def emotion_session_statistics(self, session_id: str) -> str:
        return f"{self.base_url}/emotion/session/{session_id}/statistics"
    
    # ============================================================================
    # STRESS ANALYSIS
    # ============================================================================
    
    @property
    def stress_calculate(self) -> str:
        return f"{self.base_url}/stress/calculate"
    
    def stress_history(self, user_id: str) -> str:
        return f"{self.base_url}/stress/history/{user_id}"
    
    def stress_trend(self, user_id: str) -> str:
        return f"{self.base_url}/stress/trend/{user_id}"
    
    @property
    def stress_threshold(self) -> str:
        return f"{self.base_url}/stress/threshold"
    
    @property
    def stress_recommendation(self) -> str:
        return f"{self.base_url}/stress/recommendation"
    
    # ============================================================================
    # RECOMMENDATIONS
    # ============================================================================
    
    @property
    def recommend_task(self) -> str:
        return f"{self.base_url}/recommend/task"
    
    def recommend_multiple(self, emotion: str) -> str:
        return f"{self.base_url}/recommend/multiple/{emotion}"
    
    @property
    def recommend_tasks(self) -> str:
        return f"{self.base_url}/recommend/tasks"
    
    def recommend_zone(self, zone: str) -> str:
        return f"{self.base_url}/recommend/zone/{zone}"
    
    # ============================================================================
    # ANALYTICS
    # ============================================================================
    
    @property
    def analytics_dashboard(self) -> str:
        return f"{self.base_url}/analytics/dashboard"
    
    @property
    def analytics_emotion(self) -> str:
        return f"{self.base_url}/analytics/emotion"
    
    @property
    def analytics_stress(self) -> str:
        return f"{self.base_url}/analytics/stress"
    
    def analytics_user(self, user_id: str) -> str:
        return f"{self.base_url}/analytics/user/{user_id}"
    
    def analytics_team(self, team_id: str) -> str:
        return f"{self.base_url}/analytics/team/{team_id}"
    
    @property
    def analytics_trends_emotions(self) -> str:
        return f"{self.base_url}/analytics/trends/emotions"
    
    # ============================================================================
    # ALERTS
    # ============================================================================
    
    def alerts_user(self, user_id: str) -> str:
        return f"{self.base_url}/alerts/user/{user_id}"
    
    def alerts_team(self, team_id: str) -> str:
        return f"{self.base_url}/alerts/team/{team_id}"
    
    @property
    def alerts_acknowledge(self) -> str:
        return f"{self.base_url}/alerts/acknowledge"
    
    # ============================================================================
    # USER & TEAM MANAGEMENT
    # ============================================================================
    
    @property
    def users_create(self) -> str:
        return f"{self.base_url}/users/create"
    
    def users_get(self, user_id: str) -> str:
        return f"{self.base_url}/users/{user_id}"
    
    @property
    def teams_create(self) -> str:
        return f"{self.base_url}/teams/create"
    
    def teams_get(self, team_id: str) -> str:
        return f"{self.base_url}/teams/{team_id}"
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def set_base_url(self, url: str):
        """Update the base URL"""
        self.base_url = url.rstrip('/')
    
    def get_base_url(self) -> str:
        """Get current base URL"""
        return self.base_url


class SessionManager:
    """
    Enhanced session state manager with all required keys
    """
    
    def __init__(self):
        """Initialize session state with all required keys"""
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize all session state variables"""
        
        # Authentication
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        
        if "is_authenticated" not in st.session_state:
            st.session_state.is_authenticated = False
        
        # User information
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        
        if "user_name" not in st.session_state:
            st.session_state.user_name = None
        
        if "user_email" not in st.session_state:
            st.session_state.user_email = None
        
        if "user_role" not in st.session_state:
            st.session_state.user_role = "employee"
        
        if "login_time" not in st.session_state:
            st.session_state.login_time = None
        
        # Emotion & Stress
        if "current_emotion" not in st.session_state:
            st.session_state.current_emotion = None
        
        if "stress_score" not in st.session_state:
            st.session_state.stress_score = 0
        
        # Session management
        if "session_id" not in st.session_state:
            st.session_state.session_id = None
        
        if "session_active" not in st.session_state:
            st.session_state.session_active = False
        
        # Camera
        if "camera_active" not in st.session_state:
            st.session_state.camera_active = False
        
        if "camera_component" not in st.session_state:
            st.session_state.camera_component = None
        
        # Navigation
        if "page" not in st.session_state:
            st.session_state.page = "login"
        
        # UI state
        if "show_tips" not in st.session_state:
            st.session_state.show_tips = False
        
        if "auto_refresh" not in st.session_state:
            st.session_state.auto_refresh = False
        
        # Detection history
        if "detection_history" not in st.session_state:
            st.session_state.detection_history = []
        
        # Context data
        if "stress_context" not in st.session_state:
            st.session_state.stress_context = {}
        
        # User settings
        if "user_settings" not in st.session_state:
            st.session_state.user_settings = {}
    
    # ========================================================================
    # AUTHENTICATION METHODS
    # ========================================================================
    
    def login(self, user_id: str, user_name: str = None, user_email: str = None, user_role: str = "employee"):
        """
        Log in a user
        
        Args:
            user_id: User ID
            user_name: User's display name
            user_email: User's email
            user_role: User's role (employee/manager/hr/admin)
        """
        st.session_state.user_id = user_id
        st.session_state.user_name = user_name or user_id
        st.session_state.user_email = user_email
        st.session_state.user_role = user_role
        st.session_state.logged_in = True
        st.session_state.is_authenticated = True
        st.session_state.login_time = datetime.now()
        
        # Set default page based on role
        if user_role in ['hr', 'admin']:
            st.session_state.page = "hr_dashboard"
        else:
            st.session_state.page = "employee_dashboard"
    
    def logout(self):
        """Log out the current user and clear all session data"""
        # Keep only essential keys
        keys_to_keep = ['page']
        
        # Clear all other keys
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        
        # Reinitialize
        self._initialize_session_state()
        st.session_state.page = "login"
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return st.session_state.get('logged_in', False)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (alias for is_logged_in)"""
        return self.is_logged_in()
    
    def check_session_timeout(self, timeout_minutes: int = 60) -> bool:
        """
        Check if session has timed out
        
        Args:
            timeout_minutes: Timeout duration in minutes
        
        Returns:
            bool: True if timed out, False otherwise
        """
        if not self.is_logged_in():
            return True
        
        login_time = st.session_state.get('login_time')
        if not login_time:
            return True
        
        elapsed = (datetime.now() - login_time).total_seconds() / 60
        return elapsed > timeout_minutes
    
    # ========================================================================
    # USER METHODS
    # ========================================================================
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return st.session_state.get('user_id')
    
    def get_user_name(self) -> Optional[str]:
        """Get current user name"""
        return st.session_state.get('user_name')
    
    def get_user_email(self) -> Optional[str]:
        """Get current user email"""
        return st.session_state.get('user_email')
    
    def get_user_role(self) -> str:
        """Get current user role"""
        return st.session_state.get('user_role', 'employee')
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.get_user_role() in ['admin', 'hr']
    
    # ========================================================================
    # EMOTION & STRESS METHODS
    # ========================================================================
    
    def set_current_emotion(self, emotion: str):
        """Set current detected emotion"""
        st.session_state.current_emotion = emotion
    
    def get_current_emotion(self) -> Optional[str]:
        """Get current detected emotion"""
        return st.session_state.get('current_emotion')
    
    def set_stress_score(self, score: int):
        """Set current stress score (0-10)"""
        st.session_state.stress_score = max(0, min(10, score))
    
    def get_stress_score(self) -> int:
        """Get current stress score"""
        return st.session_state.get('stress_score', 0)
    
    # ========================================================================
    # SESSION METHODS
    # ========================================================================
    
    def start_session(self, session_id: str):
        """
        Start an emotion detection session
        
        Args:
            session_id: Session ID from API
        """
        st.session_state.session_id = session_id
        st.session_state.session_active = True
        st.session_state.detection_history = []
    
    def end_session(self):
        """End current emotion detection session"""
        st.session_state.session_id = None
        st.session_state.session_active = False
    
    def is_session_active(self) -> bool:
        """Check if detection session is active"""
        return st.session_state.get('session_active', False)
    
    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return st.session_state.get('session_id')
    
    # ========================================================================
    # NAVIGATION METHODS
    # ========================================================================
    
    def set_page(self, page: str):
        """Set current page"""
        st.session_state.page = page
    
    def get_page(self) -> str:
        """Get current page"""
        return st.session_state.get('page', 'login')
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get all session state as dictionary"""
        return dict(st.session_state)
    
    def clear_detection_history(self):
        """Clear detection history"""
        st.session_state.detection_history = []
    
    def add_detection(self, detection: Dict[str, Any]):
        """Add detection to history"""
        if 'detection_history' not in st.session_state:
            st.session_state.detection_history = []
        
        st.session_state.detection_history.append(detection)
    
    def get_detection_history(self) -> list:
        """Get detection history"""
        return st.session_state.get('detection_history', [])


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Create global API endpoints instance
api_endpoints = APIEndpoints(API_BASE_URL)

# Create global session manager instance
session_manager = SessionManager()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_api_url(endpoint_name: str, **kwargs) -> str:
    """
    Get API URL for endpoint
    
    Args:
        endpoint_name: Name of endpoint (e.g., 'health', 'emotion_session_start')
        **kwargs: Additional arguments for parameterized endpoints
    
    Returns:
        str: Full API URL
    """
    # Handle parameterized endpoints
    if endpoint_name == "emotion_session_status":
        return api_endpoints.emotion_session_status(kwargs.get('session_id', ''))
    elif endpoint_name == "stress_history":
        return api_endpoints.stress_history(kwargs.get('user_id', ''))
    elif endpoint_name == "recommend_multiple":
        return api_endpoints.recommend_multiple(kwargs.get('emotion', ''))
    # Add more as needed
    
    # Handle property endpoints
    return getattr(api_endpoints, endpoint_name, api_endpoints.base_url)


def set_api_base_url(url: str):
    """
    Set custom API base URL
    
    Args:
        url: New base URL
    """
    global api_endpoints
    api_endpoints.set_base_url(url)


def get_api_base_url() -> str:
    """Get current API base URL"""
    return api_endpoints.get_base_url()


# ============================================================================
# SESSION HELPERS
# ============================================================================

def require_login():
    """Decorator-like function to check if user is logged in"""
    if not session_manager.is_logged_in():
        st.warning("⚠️ Please login to continue")
        st.session_state.page = "login"
        st.stop()


def require_admin():
    """Require admin/HR access"""
    if not session_manager.is_logged_in():
        st.warning("⚠️ Please login to continue")
        st.session_state.page = "login"
        st.stop()
    
    if not session_manager.is_admin():
        st.error("❌ Unauthorized. Admin or HR access required.")
        st.session_state.page = "employee_dashboard"
        st.stop()