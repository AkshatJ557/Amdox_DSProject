"""
Team Details Page for Amdox
Detailed team analytics and member management
"""
import streamlit as st
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'components'))

from navbar import render_navbar, render_sidebar_navigation, render_page_header
from components.charts import create_emotion_pie_chart, create_stress_trend_chart

API_BASE_URL = "http://localhost:8080"


def get_team_list():
    """Fetch list of all teams"""
    try:
        response = requests.get(f"{API_BASE_URL}/teams", timeout=10)
        if response.status_code == 200:
            return response.json().get('teams', [])
    except:
        return []


def get_team_analytics(team_id: str, days: int = 30):
    """Fetch team analytics"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analytics/team/{team_id}",
            params={"days": days},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except:
        return {}


def render_team_details():
    """Main team details page"""
    
    if 'user_id' not in st.session_state:
        st.warning("⚠️ Please login first")
        return
    
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name', 'User')
    
    render_navbar(user_id, user_name)
    selected_page = render_sidebar_navigation()
    
    if selected_page != "team":
        st.session_state.page = selected_page
        st.rerun()
    
    render_page_header("Team Details", "Team analytics and management", "👥")
    
    # Team selector
    teams = get_team_list()
    
    if not teams:
        st.warning("No teams found")
        return
    
    team_names = {t['team_id']: t['name'] for t in teams}
    selected_team = st.selectbox(
        "Select Team",
        options=list(team_names.keys()),
        format_func=lambda x: team_names[x]
    )
    
    if selected_team:
        st.markdown("---")
        
        # Fetch team analytics
        analytics = get_team_analytics(selected_team, days=30)
        
        if analytics.get('success'):
            overview = analytics.get('overview', {})
            
            # Team stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Members", overview.get('member_count', 0))
            
            with col2:
                avg_stress = overview.get('overall_avg_stress', 0)
                st.metric("Avg Stress", f"{avg_stress:.1f}/10")
            
            with col3:
                dominant = overview.get('dominant_emotion', 'Unknown')
                st.metric("Team Mood", dominant)
            
            with col4:
                high_stress = overview.get('high_stress_members', 0)
                st.metric("At Risk", high_stress)
            
            st.markdown("---")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                emotion_dist = analytics.get('emotion_analysis', {})
                if emotion_dist:
                    st.plotly_chart(
                        create_emotion_pie_chart(emotion_dist),
                        use_container_width=True
                    )
            
            with col2:
                st.markdown("### 📊 Team Members")
                members = analytics.get('members', [])
                
                for member in members[:10]:
                    st.write(f"👤 {member.get('user_id')} - Stress: {member.get('avg_stress', 0):.1f}/10")


if __name__ == "__main__":
    st.set_page_config(page_title="Team Details - Amdox", page_icon="👥", layout="wide")
    render_team_details()