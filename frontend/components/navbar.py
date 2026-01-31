"""
Enhanced Navbar Component for Amdox
Navigation bar with user menu, notifications, and quick actions
"""
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List
import requests

# API Configuration
API_BASE_URL = "http://localhost:8080"


def render_navbar(user_id: Optional[str] = None, user_name: Optional[str] = None):
    """
    Render main navigation bar
    
    Args:
        user_id: Current user ID
        user_name: Current user name
    """
    # Custom CSS for navbar
    st.markdown("""
        <style>
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .navbar-title {
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }
        .navbar-subtitle {
            color: rgba(255,255,255,0.8);
            font-size: 14px;
            margin: 0;
        }
        .user-badge {
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            color: white;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Navbar content
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
            <div class="navbar">
                <h1 class="navbar-title">🎯 Amdox</h1>
                <p class="navbar-subtitle">AI-Powered Employee Wellness System</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if user_name:
            st.markdown(f"""
                <div class="user-badge">
                    👤 {user_name}
                </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Quick actions
        render_quick_actions(user_id)


def render_sidebar_navigation():
    """
    Render sidebar navigation menu
    
    Returns:
        str: Selected page
    """
    st.sidebar.title("📋 Navigation")
    
    # Navigation options with icons
    pages = {
        "🏠 Dashboard": "dashboard",
        "📷 Emotion Detection": "detection",
        "📊 Analytics": "analytics",
        "💡 Recommendations": "recommendations",
        "👥 Team View": "team",
        "🚨 Alerts": "alerts",
        "📈 Reports": "reports",
        "⚙️ Settings": "settings"
    }
    
    # Radio button for navigation
    selected = st.sidebar.radio(
        "Go to",
        options=list(pages.keys()),
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # User info in sidebar
    render_sidebar_user_info()
    
    return pages[selected]


def render_sidebar_user_info():
    """Render user information in sidebar"""
    if 'user_id' in st.session_state:
        st.sidebar.markdown("### 👤 User Info")
        
        user_id = st.session_state.get('user_id', 'Unknown')
        user_name = st.session_state.get('user_name', 'User')
        user_role = st.session_state.get('user_role', 'employee')
        
        st.sidebar.info(f"""
        **Name:** {user_name}  
        **ID:** {user_id}  
        **Role:** {user_role.title()}
        """)
        
        # Quick stats
        if st.sidebar.button("📊 View My Stats", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        st.sidebar.warning("⚠️ Not logged in")
        
        if st.sidebar.button("🔐 Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


def render_quick_actions(user_id: Optional[str]):
    """
    Render quick action buttons
    
    Args:
        user_id: Current user ID
    """
    if not user_id:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎥 Quick Scan", use_container_width=True):
            st.session_state.quick_scan = True
            st.rerun()
    
    with col2:
        # Get unread alerts count
        alert_count = get_unread_alerts_count(user_id)
        
        alert_label = f"🚨 Alerts ({alert_count})" if alert_count > 0 else "🚨 Alerts"
        
        if st.button(alert_label, use_container_width=True):
            st.session_state.page = "alerts"
            st.rerun()
    
    with col3:
        if st.button("💡 Get Tip", use_container_width=True):
            st.session_state.show_tip = True
            st.rerun()


def get_unread_alerts_count(user_id: str) -> int:
    """
    Get count of unread alerts for user
    
    Args:
        user_id: User ID
    
    Returns:
        int: Unread alert count
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/alerts/user/{user_id}",
            params={"include_acknowledged": False},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('unacknowledged_count', 0)
    except:
        pass
    
    return 0


def render_notifications_panel(user_id: str):
    """
    Render notifications panel
    
    Args:
        user_id: User ID
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 Notifications")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/alerts/user/{user_id}",
            params={"limit": 5},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            alerts = result.get('alerts', [])
            
            if not alerts:
                st.sidebar.info("No new notifications")
            else:
                for alert in alerts:
                    severity = alert.get('severity', 'medium')
                    message = alert.get('message', 'No message')
                    created = alert.get('created_at', '')
                    
                    # Severity emoji
                    severity_emoji = {
                        'low': '💬',
                        'medium': '⚠️',
                        'high': '🚨',
                        'critical': '🔴'
                    }.get(severity, '📢')
                    
                    st.sidebar.markdown(f"{severity_emoji} {message}")
                    st.sidebar.caption(f"🕐 {created[:16]}")
                    st.sidebar.markdown("---")
    except:
        st.sidebar.error("Could not load notifications")


def render_breadcrumbs(pages: List[str]):
    """
    Render breadcrumb navigation
    
    Args:
        pages: List of page names in hierarchy
    """
    breadcrumb = " > ".join(pages)
    st.markdown(f"**Navigation:** {breadcrumb}")


def render_page_header(title: str, subtitle: Optional[str] = None, icon: str = "📊"):
    """
    Render consistent page header
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Page icon
    """
    st.markdown(f"# {icon} {title}")
    
    if subtitle:
        st.caption(subtitle)
    
    st.markdown("---")


def render_action_bar(actions: Dict[str, callable]):
    """
    Render action bar with buttons
    
    Args:
        actions: Dict of button_label -> callback function
    """
    cols = st.columns(len(actions))
    
    for idx, (label, callback) in enumerate(actions.items()):
        with cols[idx]:
            if st.button(label, use_container_width=True):
                callback()


def render_status_bar():
    """Render system status bar"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Check system status
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        
        if response.status_code == 200:
            health = response.json()
            
            with col1:
                st.success("✅ API: Online")
            
            with col2:
                db_status = health.get('database', 'unknown')
                if db_status == 'healthy':
                    st.success("✅ DB: Connected")
                else:
                    st.error("❌ DB: Offline")
            
            with col3:
                model_status = health.get('services', {}).get('emotion_detection', False)
                if model_status:
                    st.success("✅ Model: Loaded")
                else:
                    st.warning("⚠️ Model: Not Ready")
            
            with col4:
                st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        else:
            with col1:
                st.error("❌ API: Offline")
    except:
        with col1:
            st.error("❌ System: Unreachable")


def render_theme_toggle():
    """Render theme toggle in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 Appearance")
    
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    theme = st.sidebar.radio(
        "Theme",
        options=['Light', 'Dark'],
        index=0 if st.session_state.theme == 'light' else 1,
        horizontal=True
    )
    
    if theme.lower() != st.session_state.theme:
        st.session_state.theme = theme.lower()
        st.rerun()


def render_help_menu():
    """Render help menu in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ❓ Help & Support")
    
    with st.sidebar.expander("📖 Quick Guide"):
        st.markdown("""
        **Getting Started:**
        1. Start emotion detection session
        2. Allow camera access
        3. View real-time results
        4. Check recommendations
        
        **Features:**
        - Real-time emotion detection
        - Stress level monitoring
        - Task recommendations
        - Team analytics
        """)
    
    with st.sidebar.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Camera not working?**
        - Check browser permissions
        - Ensure good lighting
        - Try different browser
        
        **API errors?**
        - Refresh the page
        - Check internet connection
        - Contact support
        """)
    
    if st.sidebar.button("📧 Contact Support", use_container_width=True):
        st.sidebar.info("Email: support@amdox.com")


def render_footer():
    """Render footer"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("© 2026 Amdox Team")
    
    with col2:
        st.caption("Version 1.0.0")
    
    with col3:
        st.caption("[Documentation](#) | [Privacy](#)")


def render_mobile_menu():
    """Render mobile-friendly menu"""
    with st.sidebar:
        st.markdown("### 📱 Mobile Menu")
        
        menu_items = [
            ("🏠", "Home"),
            ("📷", "Scan"),
            ("📊", "Stats"),
            ("⚙️", "Settings")
        ]
        
        cols = st.columns(len(menu_items))
        
        for idx, (icon, label) in enumerate(menu_items):
            with cols[idx]:
                if st.button(icon, help=label, use_container_width=True):
                    st.session_state.page = label.lower()
                    st.rerun()


if __name__ == "__main__":
    # For testing
    st.set_page_config(page_title="Amdox", layout="wide")
    
    render_navbar("test_user_001", "John Doe")
    
    selected_page = render_sidebar_navigation()
    
    st.write(f"Selected page: {selected_page}")
    
    render_status_bar()
    
    render_footer()