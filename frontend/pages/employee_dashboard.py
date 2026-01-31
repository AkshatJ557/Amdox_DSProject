"""
Enhanced Employee Dashboard for Amdox
Main dashboard with real-time metrics and quick access
"""
import streamlit as st
import requests
from datetime import datetime, timedelta
import sys
import os

# Add components to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'components'))

from navbar import render_navbar, render_sidebar_navigation, render_page_header
from charts import (
    create_emotion_pie_chart,
    create_stress_trend_chart,
    create_stress_gauge,
    render_dashboard_metrics
)
from forms import render_quick_check_in_form

# API Configuration
API_BASE_URL = "http://localhost:8080"


def fetch_user_activity(user_id: str, days: int = 7):
    """
    Fetch user activity report from API
    
    Args:
        user_id: User ID
        days: Number of days
    
    Returns:
        dict: Activity report or None
    """
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
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {e}")
        return None


def render_welcome_section(user_name: str):
    """
    Render welcome section with greeting
    
    Args:
        user_name: User's name
    """
    current_hour = datetime.now().hour
    
    if current_hour < 12:
        greeting = "Good Morning"
        emoji = "🌅"
    elif current_hour < 18:
        greeting = "Good Afternoon"
        emoji = "☀️"
    else:
        greeting = "Good Evening"
        emoji = "🌙"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"## {emoji} {greeting}, {user_name}!")
        st.caption(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    
    with col2:
        if st.button("🎯 Quick Scan", use_container_width=True, type="primary"):
            st.session_state.page = "detection"
            st.rerun()


def render_quick_stats(user_id: str):
    """
    Render quick statistics cards
    
    Args:
        user_id: User ID
    """
    st.markdown("### 📊 Today's Overview")
    
    # Fetch today's data
    activity = fetch_user_activity(user_id, days=1)
    
    if activity:
        stats = activity.get('statistics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sessions = stats.get('total_sessions', 0)
            st.metric(
                "Sessions Today",
                sessions,
                delta=None,
                help="Emotion detection sessions"
            )
        
        with col2:
            detections = stats.get('total_detections', 0)
            st.metric(
                "Detections",
                detections,
                help="Total emotion detections"
            )
        
        with col3:
            avg_stress = stats.get('avg_stress', 0)
            stress_change = stats.get('stress_change', 0)
            
            st.metric(
                "Avg Stress",
                f"{avg_stress:.1f}/10",
                delta=f"{stress_change:+.1f}",
                delta_color="inverse",
                help="Average stress level"
            )
        
        with col4:
            wellness = stats.get('wellness_score', 0)
            st.metric(
                "Wellness Score",
                f"{wellness}/100",
                help="Overall wellness indicator"
            )
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sessions Today", "0")
        with col2:
            st.metric("Detections", "0")
        with col3:
            st.metric("Avg Stress", "N/A")
        with col4:
            st.metric("Wellness Score", "N/A")


def render_current_status(user_id: str):
    """
    Render current emotional and stress status
    
    Args:
        user_id: User ID
    """
    st.markdown("### 🎭 Current Status")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Latest emotion and stress
        activity = fetch_user_activity(user_id, days=1)
        
        if activity and activity.get('latest_entry'):
            latest = activity['latest_entry']
            emotion = latest.get('dominant_emotion', 'Unknown')
            stress = latest.get('stress_score', 0)
            timestamp = latest.get('timestamp', '')
            
            # Emotion emoji
            emotion_emojis = {
                'Happy': '😊',
                'Sad': '😢',
                'Angry': '😠',
                'Fear': '😰',
                'Surprise': '😲',
                'Disgust': '🤢',
                'Neutral': '😐'
            }
            
            emoji = emotion_emojis.get(emotion, '😐')
            
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <div style="font-size: 60px;">{emoji}</div>
                <h3>{emotion}</h3>
                <p style="color: #666;">Last detected</p>
                <small>{timestamp[:16] if timestamp else 'N/A'}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Display stress gauge
            st.plotly_chart(
                create_stress_gauge(stress),
                use_container_width=True,
                key="current_stress_gauge"
            )
        else:
            st.info("ℹ️ No recent detection data available. Start a session to see your status!")
    
    with col2:
        # Quick check-in
        st.markdown("#### ✍️ Quick Check-in")
        render_quick_check_in_form(user_id)


def render_emotion_summary(user_id: str, days: int = 7):
    """
    Render emotion distribution summary
    
    Args:
        user_id: User ID
        days: Number of days
    """
    st.markdown(f"### 😊 Emotion Summary (Last {days} Days)")
    
    activity = fetch_user_activity(user_id, days=days)
    
    if activity and activity.get('emotion_distribution'):
        emotion_dist = activity['emotion_distribution']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Pie chart
            st.plotly_chart(
                create_emotion_pie_chart(emotion_dist),
                use_container_width=True,
                key="emotion_pie"
            )
        
        with col2:
            # Emotion breakdown
            st.markdown("#### Breakdown")
            
            total = sum(emotion_dist.values())
            
            for emotion, count in sorted(emotion_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                st.progress(percentage / 100)
                st.caption(f"{emotion}: {count} ({percentage:.1f}%)")
    else:
        st.info("ℹ️ No emotion data available for this period")


def render_stress_analysis(user_id: str, days: int = 7):
    """
    Render stress trend analysis
    
    Args:
        user_id: User ID
        days: Number of days
    """
    st.markdown(f"### 📈 Stress Analysis (Last {days} Days)")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/stress/history/{user_id}",
            params={"limit": 50, "include_analytics": True},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                history = result.get('history', [])
                analytics = result.get('analytics', {})
                
                if history:
                    # Stress trend chart
                    st.plotly_chart(
                        create_stress_trend_chart(history, 'timestamp', 'stress_score'),
                        use_container_width=True,
                        key="stress_trend"
                    )
                    
                    # Analytics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Average", f"{analytics.get('average', 0):.1f}/10")
                    
                    with col2:
                        st.metric("Maximum", f"{analytics.get('max', 0)}/10")
                    
                    with col3:
                        st.metric("Minimum", f"{analytics.get('min', 0)}/10")
                    
                    with col4:
                        high_count = analytics.get('high_stress_count', 0)
                        st.metric("High Stress Events", high_count)
                else:
                    st.info("ℹ️ No stress history available")
            else:
                st.error(f"❌ {result.get('error')}")
        else:
            st.error(f"❌ API error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Connection error: {e}")


def render_recommendations_section(user_id: str):
    """
    Render task recommendations section
    
    Args:
        user_id: User ID
    """
    st.markdown("### 💡 Recommended Tasks")
    
    # Get latest emotion
    activity = fetch_user_activity(user_id, days=1)
    
    if activity and activity.get('latest_entry'):
        emotion = activity['latest_entry'].get('dominant_emotion', 'Neutral')
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/recommend/multiple/{emotion}",
                params={"count": 3},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    suggestions = result.get('suggestions', [])
                    
                    for suggestion in suggestions:
                        task = suggestion.get('task', '')
                        category = suggestion.get('category', '')
                        priority = suggestion.get('priority', 'Medium')
                        
                        # Priority color
                        priority_colors = {
                            'Critical': '🔴',
                            'High': '🟠',
                            'Medium': '🟡',
                            'Low': '🟢'
                        }
                        
                        priority_icon = priority_colors.get(priority, '🟡')
                        
                        with st.expander(f"{priority_icon} {task}", expanded=False):
                            st.markdown(f"**Category:** {category}")
                            st.markdown(f"**Priority:** {priority}")
                            
                            if suggestion.get('description'):
                                st.info(suggestion['description'])
                            
                            if st.button("✅ Mark as Done", key=f"done_{task}"):
                                st.success("Task marked as complete!")
                else:
                    st.info("ℹ️ No recommendations available")
        except:
            st.info("ℹ️ Could not fetch recommendations")
    else:
        st.info("ℹ️ Start a detection session to get personalized recommendations")


def render_quick_actions():
    """Render quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎥 Start Detection", use_container_width=True, type="primary"):
            st.session_state.page = "detection"
            st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
    
    with col3:
        if st.button("📈 Full Report", use_container_width=True):
            st.session_state.page = "reports"
            st.rerun()


def main():
    """Main employee dashboard page"""
    st.set_page_config(
        page_title="Employee Dashboard - Amdox",
        page_icon="🏠",
        layout="wide"
    )
    
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        st.warning("⚠️ Please log in first")
        if st.button("🔐 Go to Login"):
            st.session_state.page = "login"
            st.rerun()
        return
    
    user_id = st.session_state.get('user_id', 'Unknown')
    user_name = st.session_state.get('user_name', 'Employee')
    
    # Render navbar
    render_navbar(user_id, user_name)
    
    # Sidebar navigation
    selected_page = render_sidebar_navigation()
    
    if selected_page != "dashboard":
        st.session_state.page = selected_page
        st.rerun()
    
    # Page header
    render_page_header(
        "Employee Dashboard",
        "Your personal wellness and productivity hub",
        "🏠"
    )
    
    # Welcome section
    render_welcome_section(user_name)
    
    st.markdown("---")
    
    # Quick stats
    render_quick_stats(user_id)
    
    st.markdown("---")
    
    # Current status
    render_current_status(user_id)
    
    st.markdown("---")
    
    # Two-column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_emotion_summary(user_id, days=7)
    
    with col2:
        render_stress_analysis(user_id, days=7)
    
    st.markdown("---")
    
    # Recommendations
    render_recommendations_section(user_id)
    
    st.markdown("---")
    
    # Quick actions
    render_quick_actions()


if __name__ == "__main__":
    main()