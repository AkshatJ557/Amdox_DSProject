"""
Enhanced Forms Component for Amdox
User input forms with validation and API integration
"""
import streamlit as st
import requests
from datetime import datetime, time
from typing import Dict, Optional, Any, List
import re

# API Configuration
API_BASE_URL = "http://localhost:8080"

# Form validation patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(re.match(EMAIL_PATTERN, email))


def render_user_registration_form():
    """
    Render user registration form
    
    Returns:
        dict: User data or None
    """
    st.markdown("### 👤 User Registration")
    
    with st.form("user_registration", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input(
                "User ID *",
                placeholder="e.g., EMP001",
                help="Unique employee identifier"
            )
            
            name = st.text_input(
                "Full Name *",
                placeholder="John Doe"
            )
            
            email = st.text_input(
                "Email *",
                placeholder="john.doe@company.com"
            )
        
        with col2:
            role = st.selectbox(
                "Role *",
                options=["employee", "manager", "hr", "admin"],
                index=0
            )
            
            team_id = st.text_input(
                "Team ID (optional)",
                placeholder="e.g., TEAM001"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                help="Leave blank for no password"
            )
        
        submitted = st.form_submit_button("📝 Register User", use_container_width=True)
        
        if submitted:
            # Validation
            if not user_id or not name or not email:
                st.error("❌ Please fill all required fields (*)")
                return None
            
            if not validate_email(email):
                st.error("❌ Invalid email format")
                return None
            
            # Create user via API
            user_data = {
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": role
            }
            
            if team_id:
                user_data["team_id"] = team_id
            
            if password:
                user_data["password"] = password
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/users/create",
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        st.success(f"✅ User {user_id} registered successfully!")
                        return user_data
                    else:
                        st.error(f"❌ {result.get('error')}")
                else:
                    st.error(f"❌ API error: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {e}")
            
            return None


def render_stress_context_form() -> Optional[Dict]:
    """
    Render stress calculation context form
    
    Returns:
        dict: Context data or None
    """
    st.markdown("### 📊 Stress Context")
    st.caption("Provide additional context for accurate stress calculation")
    
    with st.form("stress_context"):
        col1, col2 = st.columns(2)
        
        with col1:
            workload = st.slider(
                "Current Workload",
                min_value=0,
                max_value=10,
                value=5,
                help="0 = Very Low, 10 = Extremely High"
            )
            
            deadline = st.slider(
                "Deadline Pressure",
                min_value=0,
                max_value=10,
                value=5,
                help="0 = No Pressure, 10 = Critical Deadline"
            )
        
        with col2:
            work_hours = st.number_input(
                "Working Hours Today",
                min_value=0.0,
                max_value=24.0,
                value=8.0,
                step=0.5
            )
            
            sleep_hours = st.number_input(
                "Sleep Hours Last Night",
                min_value=0.0,
                max_value=24.0,
                value=7.0,
                step=0.5
            )
        
        submitted = st.form_submit_button("💾 Save Context", use_container_width=True)
        
        if submitted:
            context = {
                "workload_level": workload,
                "deadline_pressure": deadline,
                "working_hours": work_hours,
                "sleep_hours": sleep_hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            st.success("✅ Context saved!")
            return context
        
        return None


def render_session_config_form() -> Optional[Dict]:
    """
    Render emotion detection session configuration form
    
    Returns:
        dict: Session configuration or None
    """
    st.markdown("### ⚙️ Session Configuration")
    
    with st.form("session_config"):
        duration = st.number_input(
            "Session Duration (minutes)",
            min_value=1,
            max_value=120,
            value=20,
            help="Recommended: 20 minutes"
        )
        
        detection_interval = st.number_input(
            "Detection Interval (seconds)",
            min_value=1,
            max_value=60,
            value=3,
            help="Time between emotion detections"
        )
        
        save_frames = st.checkbox(
            "Save Frame Images",
            value=False,
            help="Store detected frames (requires more storage)"
        )
        
        enable_alerts = st.checkbox(
            "Enable Real-time Alerts",
            value=True,
            help="Get notifications for high stress"
        )
        
        submitted = st.form_submit_button("🎬 Configure Session", use_container_width=True)
        
        if submitted:
            config = {
                "duration_minutes": duration,
                "detection_interval_seconds": detection_interval,
                "save_frames": save_frames,
                "enable_alerts": enable_alerts
            }
            
            st.success("✅ Session configured!")
            return config
        
        return None


def render_team_creation_form():
    """
    Render team creation form
    
    Returns:
        dict: Team data or None
    """
    st.markdown("### 👥 Create Team")
    
    with st.form("team_creation", clear_on_submit=True):
        team_id = st.text_input(
            "Team ID *",
            placeholder="e.g., TEAM001",
            help="Unique team identifier"
        )
        
        team_name = st.text_input(
            "Team Name *",
            placeholder="e.g., Development Team"
        )
        
        manager_id = st.text_input(
            "Manager ID (optional)",
            placeholder="e.g., EMP001"
        )
        
        description = st.text_area(
            "Description",
            placeholder="Team description and responsibilities..."
        )
        
        members = st.text_area(
            "Member IDs (optional)",
            placeholder="Enter user IDs, one per line\nEMP002\nEMP003\nEMP004"
        )
        
        submitted = st.form_submit_button("🏢 Create Team", use_container_width=True)
        
        if submitted:
            if not team_id or not team_name:
                st.error("❌ Please fill all required fields (*)")
                return None
            
            # Parse members
            member_list = [m.strip() for m in members.split('\n') if m.strip()]
            
            team_data = {
                "team_id": team_id,
                "name": team_name,
                "members": member_list
            }
            
            if manager_id:
                team_data["manager_id"] = manager_id
            
            if description:
                team_data["description"] = description
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/teams/create",
                    json=team_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        st.success(f"✅ Team {team_id} created successfully!")
                        return team_data
                    else:
                        st.error(f"❌ {result.get('error')}")
                else:
                    st.error(f"❌ API error: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {e}")
            
            return None


def render_feedback_form(recommendation_id: str, user_id: str):
    """
    Render recommendation feedback form
    
    Args:
        recommendation_id: Recommendation ID
        user_id: User ID
    """
    st.markdown("### 💭 Feedback")
    
    with st.form("feedback_form"):
        helpful = st.radio(
            "Was this recommendation helpful?",
            options=["Yes", "No"],
            horizontal=True
        )
        
        followed = st.checkbox("I followed this recommendation")
        
        feedback_text = st.text_area(
            "Additional Comments (optional)",
            placeholder="Share your thoughts..."
        )
        
        submitted = st.form_submit_button("📤 Submit Feedback", use_container_width=True)
        
        if submitted:
            feedback_data = {
                "recommendation_id": recommendation_id,
                "user_id": user_id,
                "helpful": helpful == "Yes",
                "followed": followed,
                "feedback_text": feedback_text
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/recommend/feedback",
                    json=feedback_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Thank you for your feedback!")
                else:
                    st.error("❌ Could not submit feedback")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {e}")


def render_quick_check_in_form(user_id: str):
    """
    Render quick emotional check-in form
    
    Args:
        user_id: User ID
    """
    st.markdown("### 🎯 Quick Check-in")
    st.caption("How are you feeling right now?")
    
    with st.form("quick_checkin"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            feeling = st.select_slider(
                "Current Mood",
                options=["😠 Angry", "😢 Sad", "😐 Neutral", "🙂 Good", "😊 Great"],
                value="😐 Neutral"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            energy = st.slider("Energy", 0, 10, 5)
        
        notes = st.text_input(
            "Quick Note (optional)",
            placeholder="What's on your mind?"
        )
        
        submitted = st.form_submit_button("✅ Check In", use_container_width=True)
        
        if submitted:
            # Map feeling to emotion
            feeling_map = {
                "😠 Angry": "Angry",
                "😢 Sad": "Sad",
                "😐 Neutral": "Neutral",
                "🙂 Good": "Happy",
                "😊 Great": "Happy"
            }
            
            checkin_data = {
                "user_id": user_id,
                "feeling": feeling_map.get(feeling, "Neutral"),
                "energy_level": energy,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            st.success("✅ Check-in recorded!")
            st.session_state.last_checkin = checkin_data
            
            return checkin_data
        
        return None


def render_alert_filter_form() -> Optional[Dict]:
    """
    Render alert filtering form
    
    Returns:
        dict: Filter parameters or None
    """
    st.markdown("### 🔍 Filter Alerts")
    
    with st.form("alert_filters"):
        col1, col2 = st.columns(2)
        
        with col1:
            severity = st.multiselect(
                "Severity",
                options=["low", "medium", "high", "critical"],
                default=["high", "critical"]
            )
            
            date_from = st.date_input(
                "From Date",
                value=datetime.now().date()
            )
        
        with col2:
            acknowledged = st.selectbox(
                "Status",
                options=["All", "Unacknowledged", "Acknowledged"],
                index=1
            )
            
            date_to = st.date_input(
                "To Date",
                value=datetime.now().date()
            )
        
        submitted = st.form_submit_button("🔍 Apply Filters", use_container_width=True)
        
        if submitted:
            filters = {
                "severity": severity,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat()
            }
            
            if acknowledged != "All":
                filters["acknowledged"] = acknowledged == "Acknowledged"
            
            return filters
        
        return None


def render_report_config_form() -> Optional[Dict]:
    """
    Render analytics report configuration form
    
    Returns:
        dict: Report configuration or None
    """
    st.markdown("### 📊 Configure Report")
    
    with st.form("report_config"):
        report_type = st.selectbox(
            "Report Type",
            options=[
                "User Activity",
                "Team Performance",
                "Stress Analysis",
                "Emotion Trends",
                "Complete Overview"
            ]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            time_range = st.selectbox(
                "Time Range",
                options=["Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
                index=1
            )
        
        with col2:
            format_option = st.selectbox(
                "Export Format",
                options=["PDF", "Excel", "CSV", "JSON"]
            )
        
        include_charts = st.checkbox("Include Charts", value=True)
        include_recommendations = st.checkbox("Include Recommendations", value=True)
        
        submitted = st.form_submit_button("📥 Generate Report", use_container_width=True)
        
        if submitted:
            # Parse time range
            days_map = {
                "Last 7 days": 7,
                "Last 30 days": 30,
                "Last 90 days": 90,
                "Custom": 30  # Default
            }
            
            config = {
                "report_type": report_type,
                "days": days_map.get(time_range, 30),
                "format": format_option.lower(),
                "include_charts": include_charts,
                "include_recommendations": include_recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            st.success("✅ Report configuration saved!")
            return config
        
        return None


def render_settings_form(user_id: str):
    """
    Render user settings form
    
    Args:
        user_id: User ID
    """
    st.markdown("### ⚙️ User Settings")
    
    with st.form("user_settings"):
        st.markdown("#### Notifications")
        
        email_alerts = st.checkbox("Email Alerts", value=True)
        high_stress_alerts = st.checkbox("High Stress Alerts", value=True)
        daily_summary = st.checkbox("Daily Summary Email", value=False)
        
        st.markdown("#### Privacy")
        
        share_with_team = st.checkbox("Share data with team lead", value=True)
        anonymous_analytics = st.checkbox("Participate in anonymous analytics", value=True)
        
        st.markdown("#### Detection Settings")
        
        auto_start_session = st.checkbox("Auto-start detection on login", value=False)
        detection_frequency = st.select_slider(
            "Detection Frequency",
            options=["Low", "Medium", "High"],
            value="Medium"
        )
        
        submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)
        
        if submitted:
            settings = {
                "user_id": user_id,
                "notifications": {
                    "email_alerts": email_alerts,
                    "high_stress_alerts": high_stress_alerts,
                    "daily_summary": daily_summary
                },
                "privacy": {
                    "share_with_team": share_with_team,
                    "anonymous_analytics": anonymous_analytics
                },
                "detection": {
                    "auto_start_session": auto_start_session,
                    "frequency": detection_frequency.lower()
                }
            }
            
            st.success("✅ Settings saved!")
            st.session_state.user_settings = settings
            
            return settings


if __name__ == "__main__":
    # For testing
    st.title("📝 Forms Component Demo")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Registration",
        "Stress Context",
        "Team Creation",
        "Settings"
    ])
    
    with tab1:
        render_user_registration_form()
    
    with tab2:
        render_stress_context_form()
    
    with tab3:
        render_team_creation_form()
    
    with tab4:
        render_settings_form("test_user_001")