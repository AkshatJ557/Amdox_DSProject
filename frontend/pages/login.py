"""
Login Page for Amdox
User authentication and session initialization
"""
import streamlit as st
import requests
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8080"


def authenticate_user(user_id: str, password: str = None):
    """
    Authenticate user via API
    
    Args:
        user_id: User ID
        password: Password (optional)
    
    Returns:
        dict: User data or None
    """
    try:
        # For demo, we'll use a simple user fetch
        # In production, use proper authentication endpoint
        response = requests.get(
            f"{API_BASE_URL}/users/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None


def initialize_session(user_data: dict):
    """
    Initialize user session
    
    Args:
        user_data: User information
    """
    st.session_state.logged_in = True
    st.session_state.user_id = user_data.get('user_id')
    st.session_state.user_name = user_data.get('name', 'User')
    st.session_state.user_email = user_data.get('email', '')
    st.session_state.user_role = user_data.get('role', 'employee')
    st.session_state.login_time = datetime.now()
    
    # Set default page based on role
    if st.session_state.user_role in ['hr', 'admin']:
        st.session_state.page = "hr_dashboard"
    else:
        st.session_state.page = "employee_dashboard"


def render_login_form():
    """Render login form"""
    
    # Logo/Header
    st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1 style="color: #667eea; font-size: 48px;">🎯 Amdox</h1>
            <p style="color: #666; font-size: 18px;">AI-Powered Employee Wellness System</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login")
        
        with st.form("login_form"):
            user_id = st.text_input(
                "User ID",
                placeholder="Enter your user ID (e.g., EMP001)",
                help="Your unique employee identifier"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password (optional for demo)"
            )
            
            remember_me = st.checkbox("Remember me")
            
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted:
                if not user_id:
                    st.error("❌ Please enter your User ID")
                else:
                    with st.spinner("Authenticating..."):
                        user_data = authenticate_user(user_id, password)
                        
                        if user_data:
                            initialize_session(user_data)
                            st.success("✅ Login successful!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials. Please try again.")


def render_demo_accounts():
    """Render demo account information"""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.expander("🎭 Demo Accounts", expanded=False):
            st.markdown("""
            **Employee Account:**
            - User ID: `EMP001`
            - Password: `demo123`
            
            **Manager Account:**
            - User ID: `MGR001`
            - Password: `demo123`
            
            **HR Account:**
            - User ID: `HR001`
            - Password: `admin123`
            
            **Admin Account:**
            - User ID: `ADMIN001`
            - Password: `admin123`
            """)


def render_quick_login():
    """Render quick login buttons"""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### ⚡ Quick Login (Demo)")
        
        col_emp, col_hr = st.columns(2)
        
        with col_emp:
            if st.button("👤 Employee Demo", use_container_width=True):
                user_data = {
                    'user_id': 'EMP001',
                    'name': 'John Doe',
                    'email': 'john@company.com',
                    'role': 'employee'
                }
                initialize_session(user_data)
                st.rerun()
        
        with col_hr:
            if st.button("👔 HR Demo", use_container_width=True):
                user_data = {
                    'user_id': 'HR001',
                    'name': 'Jane Smith',
                    'email': 'jane@company.com',
                    'role': 'hr'
                }
                initialize_session(user_data)
                st.rerun()


def render_login():
    """Main login page"""
    
    # Check if already logged in
    if st.session_state.get('logged_in'):
        st.success("✅ You are already logged in!")
        
        user_name = st.session_state.get('user_name', 'User')
        st.info(f"👤 Logged in as: **{user_name}**")
        
        if st.button("🏠 Go to Dashboard"):
            page = st.session_state.get('page', 'employee_dashboard')
            st.session_state.page = page
            st.rerun()
        
        if st.button("🚪 Logout"):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        return
    
    # Render login form
    render_login_form()
    
    # Demo accounts info
    render_demo_accounts()
    
    # Quick login
    render_quick_login()
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666;">
            <p>© 2026 Amdox Team | Version 1.0.0</p>
            <p>Need help? Contact: support@amdox.com</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Login - Amdox",
        page_icon="🔐",
        layout="centered"
    )
    
    # Import time for delay
    import time
    
    render_login()