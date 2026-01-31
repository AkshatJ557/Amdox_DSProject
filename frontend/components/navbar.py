"""
Navbar component
"""
import streamlit as st
from streamlit_option_menu import option_menu

# Add parent directories to path
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
components_dir = os.path.dirname(current_dir)
app_dir = os.path.dirname(components_dir)
root_dir = os.path.dirname(app_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.session import session_manager


def show_navbar(current_page: str = "Dashboard"):
    """
    Display navigation bar
    
    Args:
        current_page: Current active page
    """
    # Custom CSS for navbar
    st.markdown("""
    <style>
    .navbar {
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation menu
    if session_manager.is_logged_in():
        with st.sidebar:
            st.title("🧠 Amdox")
            st.caption("Emotion Detection System")
            st.markdown("---")
            
            selected = option_menu(
                menu_title="Navigation",
                options=["Dashboard", "Detect Emotion", "History", "Analytics", "Settings"],
                icons=["house", "camera", "clock-history", "graph-up", "gear"],
                menu_icon="cast",
                default_index=0,
            )
            
            st.markdown("---")
            
            # User info
            st.write(f"**User:** {session_manager.get_user_id()}")
            
            if st.button("Logout"):
                session_manager.logout()
                st.rerun()
            
            # API status
            st.markdown("---")
            st.caption("API Status: 🟢 Connected")


def show_simple_navbar():
    """Show simplified navbar for pages without sidebar"""
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    
    with col1:
        st.title("🧠 Amdox")
    
    with col2:
        if st.button("Home"):
            st.switch_page("frontend.pages.employee_dashboard")
    
    with col3:
        if st.button("Detect"):
            st.session_state.show_camera = True
    
    with col4:
        if st.button("History"):
            st.session_state.show_history = True
    
    with col5:
        if session_manager.is_logged_in():
            user_id = session_manager.get_user_id()
            st.write(f"👤 {user_id}")
        else:
            if st.button("Login"):
                st.switch_page("frontend.pages.login")

