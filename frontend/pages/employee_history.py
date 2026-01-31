"""
Employee History Page - View past emotion detection records
"""
import streamlit as st
import pandas as pd
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


def employee_history():
    """Display employee history page"""
    st.set_page_config(
        page_title="History - Amdox",
        page_icon="📜",
        layout="wide"
    )
    
    # Check authentication
    if not session_manager.is_logged_in():
        st.warning("Please log in to view your history")
        st.switch_page("frontend.pages.login")
        return
    
    st.title("📜 Emotion Detection History")
    st.markdown(f"Showing records for **{session_manager.get_user_id()}**")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        date_filter = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now())
        )
    
    with col2:
        emotion_filter = st.multiselect(
            "Filter by Emotion",
            ['Happy', 'Neutral', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust']
        )
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Sample history data
    st.markdown("---")
    
    # Create sample data
    history_data = [
        {"Date": "2024-01-15 14:30", "Emotion": "Happy 😊", "Stress": 2, "Confidence": 0.95},
        {"Date": "2024-01-15 10:15", "Emotion": "Neutral 😐", "Stress": 4, "Confidence": 0.88},
        {"Date": "2024-01-14 16:45", "Emotion": "Sad 😢", "Stress": 6, "Confidence": 0.92},
        {"Date": "2024-01-14 09:00", "Emotion": "Happy 😊", "Stress": 1, "Confidence": 0.97},
        {"Date": "2024-01-13 15:30", "Emotion": "Angry 😠", "Stress": 8, "Confidence": 0.89},
        {"Date": "2024-01-13 11:00", "Emotion": "Neutral 😐", "Stress": 4, "Confidence": 0.91},
        {"Date": "2024-01-12 14:00", "Emotion": "Fear 😨", "Stress": 7, "Confidence": 0.85},
    ]
    
    df = pd.DataFrame(history_data)
    
    # Apply filters
    if emotion_filter:
        emotions_only = [e.split()[0] for e in emotion_filter]
        df = df[df['Emotion'].apply(lambda x: x.split()[0] in emotions_only)]
    
    # Display data
    st.dataframe(df, use_container_width=True)
    
    # Statistics
    st.markdown("---")
    st.subheader("📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Detections", len(df))
    
    with col2:
        avg_stress = df['Stress'].mean()
        st.metric("Avg Stress Level", f"{avg_stress:.1f}/10")
    
    with col3:
        dominant = df['Emotion'].apply(lambda x: x.split()[0]).mode()[0]
        st.metric("Most Common Emotion", dominant)
    
    with col4:
        avg_conf = df['Confidence'].mean() * 100
        st.metric("Avg Confidence", f"{avg_conf:.1f}%")
    
    # Charts
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Emotion Distribution")
        emotion_counts = df['Emotion'].apply(lambda x: x.split()[0]).value_counts()
        st.bar_chart(emotion_counts)
    
    with col2:
        st.subheader("Stress Over Time")
        stress_over_time = df.set_index('Date')['Stress']
        st.line_chart(stress_over_time)


if __name__ == "__main__":
    employee_history()

