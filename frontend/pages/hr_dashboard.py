"""
HR Dashboard - Analytics dashboard for HR managers
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
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from frontend.session import session_manager, API_BASE_URL


def hr_dashboard():
    """Display HR dashboard"""
    st.set_page_config(
        page_title="HR Dashboard - Amdox",
        page_icon="📊",
        layout="wide"
    )
    
    # Check authentication (simplified for demo)
    if not session_manager.is_logged_in():
        st.warning("Please log in to access the HR dashboard")
        st.switch_page("frontend.pages.login")
        return
    
    st.title("📊 HR Dashboard")
    st.markdown(f"Welcome, **{session_manager.get_user_id()}**!")
    
    # Sidebar filters
    st.sidebar.title("Filters")
    
    # Date range
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        help="Select date range for analytics"
    )
    
    # Team filter
    team_filter = st.sidebar.selectbox(
        "Team",
        ["All Teams", "Engineering", "Marketing", "Sales", "HR"]
    )
    
    # Refresh data button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Main dashboard content
    st.markdown("---")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Employees",
            value="156",
            delta="+5 this month"
        )
    
    with col2:
        st.metric(
            label="Avg Team Stress",
            value="4.2/10",
            delta="-0.3",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Happy Employees",
            value="68%",
            delta="+5%"
        )
    
    with col4:
        st.metric(
            label="Active Alerts",
            value="3",
            delta="-2",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎭 Team Emotion Distribution")
        
        # Sample data
        emotion_data = {
            'Emotion': ['Happy', 'Neutral', 'Sad', 'Angry', 'Fear'],
            'Count': [45, 38, 28, 25, 20]
        }
        
        df = pd.DataFrame(emotion_data)
        
        fig = px.pie(
            df, 
            values='Count', 
            names='Emotion',
            title='Emotion Distribution',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Stress Trends")
        
        # Sample data
        stress_data = {
            'Date': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, -1, -1)],
            'Stress': [4.2, 4.5, 4.1, 4.8, 4.3, 4.0, 4.2, 4.1]
        }
        
        df = pd.DataFrame(stress_data)
        
        fig = px.line(
            df,
            x='Date',
            y='Stress',
            title='Average Stress Over Time',
            markers=True
        )
        fig.add_hline(y=5, line_dash="dash", line_color="orange", annotation_text="Moderate")
        fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="High")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Team breakdown
    st.subheader("👥 Team Breakdown")
    
    # Sample team data
    team_data = pd.DataFrame({
        'Team': ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance'],
        'Employees': [45, 28, 35, 12, 18],
        'Avg Stress': [4.5, 3.8, 4.2, 3.5, 3.9],
        'Happy %': [62, 75, 65, 78, 72]
    })
    
    st.dataframe(team_data, use_container_width=True)
    
    # Alerts section
    st.markdown("---")
    st.subheader("⚠️ Recent Alerts")
    
    alerts = [
        {"Date": "2024-01-15", "Employee": "John D.", "Type": "High Stress", "Status": "Resolved"},
        {"Date": "2024-01-14", "Employee": "Sarah M.", "Type": "Low Engagement", "Status": "Pending"},
        {"Date": "2024-01-13", "Employee": "Mike R.", "Type": "High Stress", "Status": "Resolved"},
    ]
    
    alerts_df = pd.DataFrame(alerts)
    st.table(alerts_df)
    
    # Actions section
    st.markdown("---")
    st.subheader("💡 Recommended Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        ### 🧘 Wellness Program
        Consider implementing a team wellness program to reduce stress levels.
        """)
    
    with col2:
        st.info("""
        ### 📊 1:1 Meetings
        Schedule check-ins with employees showing high stress patterns.
        """)
    
    with col3:
        st.info("""
        ### 🎯 Workload Review
        Review workload distribution for high-stress teams.
        """)


if __name__ == "__main__":
    hr_dashboard()

