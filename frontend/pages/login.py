"""
Login page for Amdox
"""
import streamlit as st
import requests
import os

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


def login_page():
    """Display login page"""
    st.set_page_config(page_title="Login - Amdox", page_icon="🔐")
    
    # Check if already logged in
    if session_manager.is_logged_in():
        st.success("You are already logged in!")
        if st.button("Go to Dashboard"):
            st.switch_page("frontend.pages.employee_dashboard")
        if st.button("Logout"):
            session_manager.logout()
            st.rerun()
        return
    
    st.title("🔐 Amdox Login")
    st.markdown("Enter your credentials to access the emotion detection system")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                # Attempt login (in a real app, this would validate credentials)
                success, result = authenticate_user(username, password)
                
                if success:
                    session_manager.login(username)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(f"Login failed: {result}")
            else:
                st.warning("Please enter both username and password")
    
    # Demo mode option
    st.markdown("---")
    st.subheader("Demo Mode")
    st.info("Want to explore without logging in?")
    
    if st.button("Continue as Guest"):
        session_manager.login("guest_user")
        st.success("Guest mode activated!")
        st.rerun()
    
    # Check backend connection
    st.markdown("---")
    st.subheader("System Status")
    
    if st.button("Check API Connection"):
        check_api_connection()


def authenticate_user(username: str, password: str) -> tuple:
    """
    Authenticate user with backend API
    
    Args:
        username: Username
        password: Password
    
    Returns:
        tuple: (success, message)
    """
    try:
        # In a real app, this would call the authentication API
        # For demo purposes, accept any non-empty credentials
        if len(username) >= 3 and len(password) >= 6:
            return True, "Authentication successful"
        else:
            return False, "Invalid credentials"
            
    except Exception as e:
        return False, f"Authentication error: {str(e)}"


def check_api_connection():
    """Check if backend API is reachable"""
    try:
        health_url = f"{API_BASE_URL}/health"
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ API Connected: {data.get('status', 'unknown')}")
            st.json(data)
        else:
            st.error(f"❌ API returned status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to API. Make sure the backend server is running.")
        st.info("💡 Start the backend with: python run.py")
    except Exception as e:
        st.error(f"❌ Error connecting to API: {str(e)}")


if __name__ == "__main__":
    login_page()

