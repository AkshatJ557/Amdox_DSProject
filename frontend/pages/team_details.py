"""
Team Details Page - View individual team analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Add parent directories to path
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.dirname(current_dir)
components_dir = os.path.dirname(pages_dir)
app_dir = os.path.dirname(components_dir)
root_dir = os.path.dirname(app_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.session import session_manager


def team_details():
    """Display team details page"""
    st.set_page_config(
        page_title="Team Details - Amdox",
        page_icon="👥",
        layout="wide"
    )
    
    # Check authentication
    if not session_manager.is_logged_in():
        st.warning("Please log in to view team details")
        st.switch_page("frontend.pages.login")
        return
    
    st.title("👥 Team Details")
    
    # Team selector
    col1, col2 = st.columns([2, 1])
    
    with col1:
        team_id = st.selectbox(
            "Select Team",
            ["Engineering", "Marketing", "Sales", "HR", "Finance", "Product"]
        )
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    st.markdown("---")
    
    # Team metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Team Members", "45")
    
    with col2:
        st.metric("Avg Stress", "4.5/10")
    
    with col3:
        st.metric("Happy %", "62%")
    
    with col4:
        st.metric("Active Alerts", "2")
    
    st.markdown("---")
    
    # Team members table
    st.subheader("👤 Team Members")
    
    # Sample member data
    members_data = [
        {"Name": "John Doe", "Role": "Engineer", "Avg Stress": 4.2, "Happy %": 65, "Last Active": "Today"},
        {"Name": "Jane Smith", "Role": "Senior Engineer", "Avg Stress": 3.8, "Happy %": 72, "Last Active": "Today"},
        {"Name": "Mike Johnson", "Role": "Engineer", "Avg Stress": 5.1, "Happy %": 58, "Last Active": "Yesterday"},
        {"Name": "Sarah Williams", "Role": "Tech Lead", "Avg Stress": 4.5, "Happy %": 68, "Last Active": "Today"},
        {"Name": "Chris Brown", "Role": "Engineer", "Avg Stress": 3.9, "Happy %": 70, "Last Active": "Today"},
    ]
    
    df = pd.DataFrame(members_data)
    st.dataframe(df, use_container_width=True)
    
    # Charts
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎭 Team Emotion Distribution")
        emotion_data = {
            'Emotion': ['Happy', 'Neutral', 'Sad', 'Angry', 'Fear'],
            'Percentage': [35, 30, 15, 12, 8]
        }
        df_emotions = pd.DataFrame(emotion_data)
        fig = px.pie(
            df_emotions,
            values='Percentage',
            names='Emotion',
            title='Team Emotion Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Stress Trend (Last 7 Days)")
        stress_data = {
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Avg Stress': [4.2, 4.5, 4.3, 4.8, 4.4, 4.0, 3.8]
        }
        df_stress = pd.DataFrame(stress_data)
        fig = px.line(
            df_stress,
            x='Day',
            y='Avg Stress',
            markers=True
        )
        fig.add_hline(y=5, line_dash="dash", line_color="orange")
        fig.add_hline(y=7, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    # Alerts section
    st.markdown("---")
    st.subheader("⚠️ Team Alerts")
    
    alerts = [
        {"Date": "2024-01-15", "Member": "Mike Johnson", "Type": "High Stress", "Status": "Under Review"},
        {"Date": "2024-01-14", "Member": "Sarah Williams", "Type": "Decreased Engagement", "Status": "Resolved"},
    ]
    
    st.table(alerts)
    
    # Actions
    st.markdown("---")
    st.subheader("💡 Team Lead Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Send Wellness Tips"):
            st.success("Wellness tips sent to team!")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.success("Report generation started!")
    
    with col3:
        if st.button("👥 Schedule Team Check-in"):
            st.success("Check-in meeting scheduled!")


if __name__ == "__main__":
    team_details()

