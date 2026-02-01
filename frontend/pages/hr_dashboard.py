"""
HR Dashboard Page for Amdox
Organization-wide monitoring and management
"""
import streamlit as st
import requests
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'components'))

from navbar import render_navbar, render_sidebar_navigation, render_page_header
from components.charts import create_team_comparison_chart, create_emotion_pie_chart
from components.forms import render_user_registration_form, render_team_creation_form
API_BASE_URL = "http://localhost:8080"


def check_hr_access():
    """Check if user has HR/Admin access"""
    role = st.session_state.get('user_role', 'employee')
    if role not in ['hr', 'admin']:
        st.error("❌ Unauthorized. HR or Admin access required.")
        st.session_state.page = "employee_dashboard"
        st.rerun()


def render_system_overview():
    """Render system-wide statistics"""
    st.markdown("### 📊 System Overview")
    
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/dashboard", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                overview = data.get('overview', {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Users", overview.get('total_users', 0))
                
                with col2:
                    st.metric("Active Sessions", overview.get('active_sessions', 0))
                
                with col3:
                    avg_stress = overview.get('avg_stress', 0)
                    st.metric("System Avg Stress", f"{avg_stress:.1f}/10")
                
                with col4:
                    alerts = overview.get('active_alerts', 0)
                    st.metric("Active Alerts", alerts)
    except Exception as e:
        st.error(f"Error loading overview: {e}")


def render_high_risk_users():
    """Render high-risk users table"""
    st.markdown("### 🚨 High-Risk Employees")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/analytics/stress",
            params={"days": 7},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                high_risk = result.get('high_risk_users', [])
                
                if high_risk:
                    for user in high_risk[:10]:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"👤 {user.get('user_id')}")
                        
                        with col2:
                            stress = user.get('avg_stress', 0)
                            st.write(f"💊 {stress:.1f}/10")
                        
                        with col3:
                            count = user.get('high_stress_count', 0)
                            st.write(f"🚨 {count} events")
                else:
                    st.success("✅ No high-risk employees")
    except Exception as e:
        st.error(f"Error: {e}")


def render_hr_dashboard():
    """Main HR dashboard page"""
    
    # Check access
    check_hr_access()
    
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name', 'HR')
    
    render_navbar(user_id, user_name)
    selected_page = render_sidebar_navigation()
    
    if selected_page != "dashboard":
        st.session_state.page = selected_page
        st.rerun()
    
    render_page_header("HR Dashboard", "Organization-wide monitoring", "👔")
    
    # System overview
    render_system_overview()
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚨 Alerts",
        "👥 Users",
        "🏢 Teams",
        "📊 Analytics"
    ])
    
    with tab1:
        render_high_risk_users()
    
    with tab2:
        st.markdown("### 👥 User Management")
        render_user_registration_form()
    
    with tab3:
        st.markdown("### 🏢 Team Management")
        render_team_creation_form()
    
    with tab4:
        st.markdown("### 📊 System Analytics")
        st.info("Advanced analytics coming soon!")


if __name__ == "__main__":
    st.set_page_config(page_title="HR Dashboard - Amdox", page_icon="👔", layout="wide")
    render_hr_dashboard()