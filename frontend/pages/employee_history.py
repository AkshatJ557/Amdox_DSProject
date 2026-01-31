"""
Enhanced Employee History Page for Amdox
View past sessions, emotion timeline, and historical data
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add components to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'components'))

from navbar import render_navbar, render_sidebar_navigation, render_page_header
from charts import (
    create_emotion_timeline,
    create_emotion_bar_chart,
    create_stress_trend_chart,
    create_box_plot
)

# API Configuration
API_BASE_URL = "http://localhost:8080"


def fetch_user_history(user_id: str, days: int = 30):
    """Fetch user historical data"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analytics/user/{user_id}",
            params={"days": days},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result
        return None
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None


def render_session_history(user_id: str):
    """Render past sessions table"""
    st.markdown("### 📋 Session History")
    
    history = fetch_user_history(user_id, days=30)
    
    if history and history.get('sessions'):
        sessions = history['sessions']
        
        # Create DataFrame
        df_sessions = pd.DataFrame(sessions)
        
        # Format columns
        if 'timestamp' in df_sessions.columns:
            df_sessions['timestamp'] = pd.to_datetime(df_sessions['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display table
        st.dataframe(
            df_sessions[[
                'session_id', 'timestamp', 'dominant_emotion',
                'avg_stress', 'detection_count'
            ]].rename(columns={
                'session_id': 'Session ID',
                'timestamp': 'Date & Time',
                'dominant_emotion': 'Dominant Emotion',
                'avg_stress': 'Avg Stress',
                'detection_count': 'Detections'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = df_sessions.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            "session_history.csv",
            "text/csv"
        )
    else:
        st.info("ℹ️ No session history available")


def render_emotion_timeline_section(user_id: str, days: int):
    """Render emotion timeline"""
    st.markdown(f"### 📅 Emotion Timeline (Last {days} Days)")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/stress/history/{user_id}",
            params={"limit": 100},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                history = result.get('history', [])
                
                if history:
                    # Prepare data for timeline
                    timeline_data = [
                        {
                            'timestamp': entry['timestamp'],
                            'emotion': entry.get('dominant_emotion', 'Unknown')
                        }
                        for entry in history
                    ]
                    
                    st.plotly_chart(
                        create_emotion_timeline(timeline_data),
                        use_container_width=True
                    )
                else:
                    st.info("ℹ️ No timeline data available")
    except Exception as e:
        st.error(f"❌ Error loading timeline: {e}")


def render_statistics_summary(user_id: str, days: int):
    """Render statistics summary"""
    st.markdown(f"### 📊 Statistics Summary (Last {days} Days)")
    
    history = fetch_user_history(user_id, days=days)
    
    if history:
        stats = history.get('statistics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sessions = stats.get('total_sessions', 0)
            st.metric("Total Sessions", total_sessions)
        
        with col2:
            total_detections = stats.get('total_detections', 0)
            st.metric("Total Detections", total_detections)
        
        with col3:
            avg_stress = stats.get('avg_stress', 0)
            st.metric("Average Stress", f"{avg_stress:.1f}/10")
        
        with col4:
            wellness = stats.get('wellness_score', 0)
            st.metric("Wellness Score", f"{wellness}/100")


def render_detailed_analysis(user_id: str, days: int):
    """Render detailed analysis charts"""
    st.markdown("### 🔍 Detailed Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Emotion Distribution", "Stress Trends", "Patterns"])
    
    with tab1:
        history = fetch_user_history(user_id, days=days)
        
        if history and history.get('emotion_distribution'):
            st.plotly_chart(
                create_emotion_bar_chart(history['emotion_distribution']),
                use_container_width=True
            )
    
    with tab2:
        try:
            response = requests.get(
                f"{API_BASE_URL}/stress/trend/{user_id}",
                params={"days": days, "granularity": "daily"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    trend_data = result.get('trend_data', [])
                    
                    if trend_data:
                        st.plotly_chart(
                            create_stress_trend_chart(
                                trend_data,
                                'timestamp',
                                'avg_stress'
                            ),
                            use_container_width=True
                        )
        except:
            st.info("ℹ️ Could not load stress trends")
    
    with tab3:
        st.info("📊 Pattern analysis coming soon!")


def main():
    """Main employee history page"""
    st.set_page_config(
        page_title="Employee History - Amdox",
        page_icon="📜",
        layout="wide"
    )
    
    # Check login
    if 'user_id' not in st.session_state:
        st.warning("⚠️ Please log in first")
        return
    
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name', 'Employee')
    
    # Navbar
    render_navbar(user_id, user_name)
    
    # Sidebar
    selected_page = render_sidebar_navigation()
    
    if selected_page != "dashboard":
        st.session_state.page = selected_page
        st.rerun()
    
    # Header
    render_page_header(
        "History & Analytics",
        "View your past sessions and trends",
        "📜"
    )
    
    # Time range selector
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📅 Select Time Range")
    
    with col2:
        days = st.selectbox(
            "Period",
            options=[7, 14, 30, 60, 90],
            format_func=lambda x: f"Last {x} days",
            index=2
        )
    
    st.markdown("---")
    
    # Statistics summary
    render_statistics_summary(user_id, days)
    
    st.markdown("---")
    
    # Session history
    render_session_history(user_id)
    
    st.markdown("---")
    
    # Emotion timeline
    render_emotion_timeline_section(user_id, days)
    
    st.markdown("---")
    
    # Detailed analysis
    render_detailed_analysis(user_id, days)


if __name__ == "__main__":
    main()