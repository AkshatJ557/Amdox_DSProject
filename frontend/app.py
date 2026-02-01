"""
Amdox Main Application - FIXED VERSION
Multi-page Streamlit app with navigation and routing
"""
import streamlit as st
import sys
import os

# Add pages directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.join(current_dir, 'pages')
components_dir = os.path.join(current_dir, 'components')

if pages_dir not in sys.path:
    sys.path.insert(0, pages_dir)

if components_dir not in sys.path:
    sys.path.insert(0, components_dir)

# Import page modules (not individual functions)
import pages.login as login_module
import pages.employee_dashboard as dashboard_module
import pages.employee_history as history_module
import pages.employee_session as session_module
import pages.hr_dashboard as hr_module
import pages.team_details as team_module


# Page configuration
st.set_page_config(
    page_title="Amdox - AI-Powered Employee Wellness",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom button styles */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #667eea;
        color: white;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        background-color: #764ba2;
        color: white;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


# Page routing - reference module functions correctly
PAGES = {
    "login": {
        "title": "Login",
        "icon": "🔐",
        "function": login_module.render_login,
        "auth_required": False
    },
    "employee_dashboard": {
        "title": "Dashboard",
        "icon": "🏠",
        "function": dashboard_module.render_employee_dashboard,
        "auth_required": True
    },
    "employee_history": {
        "title": "History",
        "icon": "📊",
        "function": history_module.render_employee_history,
        "auth_required": True
    },
    "employee_session": {
        "title": "Detection",
        "icon": "🎥",
        "function": session_module.render_employee_session,
        "auth_required": True
    },
    "hr_dashboard": {
        "title": "HR Dashboard",
        "icon": "👔",
        "function": hr_module.render_hr_dashboard,
        "auth_required": True
    },
    "team_details": {
        "title": "Team Details",
        "icon": "👥",
        "function": team_module.render_team_details,
        "auth_required": True
    }
}


def initialize_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'employee'
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    
    if 'session_active' not in st.session_state:
        st.session_state.session_active = False
    
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False


def check_authentication(page_config):
    """
    Check if user is authenticated for the requested page
    
    Args:
        page_config: Page configuration dict
    
    Returns:
        bool: True if authorized, False otherwise
    """
    if not page_config.get('auth_required', False):
        return True
    
    if not st.session_state.get('logged_in', False):
        st.session_state.page = 'login'
        return False
    
    return True


def render_page():
    """Render the current page"""
    
    # Get current page
    current_page = st.session_state.get('page', 'login')
    
    # Check if page exists
    if current_page not in PAGES:
        st.error(f"❌ Page '{current_page}' not found")
        st.session_state.page = 'login'
        st.rerun()
        return
    
    page_config = PAGES[current_page]
    
    # Check authentication
    if not check_authentication(page_config):
        st.warning("⚠️ Please login to continue")
        login_module.render_login()
        return
    
    # Render the page
    try:
        page_config['function']()
    except Exception as e:
        st.error(f"❌ Error rendering page: {e}")
        st.exception(e)


def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Render current page
    render_page()


if __name__ == "__main__":
    main()