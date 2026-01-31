"""
Charts and visualization components
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def display_emotion_chart(emotions: dict, title: str = "Emotion Distribution"):
    """
    Display emotion distribution as a chart
    
    Args:
        emotions: Dictionary of emotion names and counts
        title: Chart title
    """
    if not emotions:
        st.info("No emotion data to display")
        return
    
    df = pd.DataFrame(list(emotions.items()), columns=['Emotion', 'Count'])
    
    # Create bar chart
    fig = px.bar(
        df, 
        x='Emotion', 
        y='Count',
        title=title,
        color='Emotion',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_stress_chart(stress_history: list, title: str = "Stress Over Time"):
    """
    Display stress levels over time as a line chart
    
    Args:
        stress_history: List of dictionaries with 'timestamp' and 'score'
        title: Chart title
    """
    if not stress_history:
        st.info("No stress data to display")
        return
    
    df = pd.DataFrame(stress_history)
    
    fig = px.line(
        df, 
        x='timestamp', 
        y='score',
        title=title,
        markers=True
    )
    
    # Add threshold line
    fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="High Stress Threshold")
    fig.add_hline(y=3, line_dash="dash", line_color="orange", annotation_text="Moderate Stress Threshold")
    
    st.plotly_chart(fig, use_container_width=True)


def display_recommendation_card(recommendation: dict):
    """
    Display a recommendation card
    
    Args:
        recommendation: Dictionary with recommendation details
    """
    if not recommendation:
        return
    
    task = recommendation.get('task', 'No recommendation available')
    category = recommendation.get('category', 'General')
    priority = recommendation.get('priority', 'Medium')
    duration = recommendation.get('duration', 'N/A')
    
    # Set color based on priority
    priority_colors = {
        'Critical': '🔴',
        'High': '🟠',
        'Medium-High': '🟡',
        'Medium': '🟢',
        'Low': '🔵'
    }
    
    priority_emoji = priority_colors.get(priority, '⚪')
    
    st.success(f"""
    ### 💡 {task}
    
    **Category:** {category} | **Priority:** {priority_emoji} {priority} | **Duration:** {duration}
    """)


def display_emotion_gauge(emotion: str, confidence: float):
    """
    Display emotion confidence as a gauge
    
    Args:
        emotion: Detected emotion
        confidence: Confidence score (0-1)
    """
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Detected: {emotion}"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "lightyellow"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)


def display_stress_meter(score: int):
    """
    Display stress score as a visual meter
    
    Args:
        score: Stress score (0-10)
    """
    # Define colors for different stress levels
    if score >= 8:
        color = "red"
        level = "Very High"
    elif score >= 6:
        color = "orange"
        level = "High"
    elif score >= 4:
        color = "yellow"
        level = "Moderate"
    else:
        color = "green"
        level = "Low"
    
    # Create progress bar
    st.write(f"**Stress Level: {level}** ({score}/10)")
    st.progress(score * 10, text=f"{score}/10")
    
    # Show color indicator
    st.markdown(f"""
    <div style="
        background-color: {color};
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        color: white;
        font-weight: bold;
    ">
        {level} STRESS
    </div>
    """, unsafe_allow_html=True)


def display_team_overview(team_data: dict):
    """
    Display team overview statistics
    
    Args:
        team_data: Dictionary with team statistics
    """
    if not team_data:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Team Members",
            value=team_data.get('member_count', 0)
        )
    
    with col2:
        st.metric(
            label="Avg Stress",
            value=f"{team_data.get('avg_stress', 0):.1f}/10"
        )
    
    with col3:
        st.metric(
            label="Happy %",
            value=f"{team_data.get('happy_percentage', 0):.1f}%"
        )
    
    with col4:
        st.metric(
            label="Alerts Today",
            value=team_data.get('alert_count', 0)
        )


def display_heatmap(data: dict, title: str = "Activity Heatmap"):
    """
    Display activity heatmap
    
    Args:
        data: Dictionary with time-based activity data
        title: Chart title
    """
    if not data:
        st.info("No data for heatmap")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(list(data.items()), columns=['Time', 'Activity'])
    
    fig = px.density_heatmap(
        df,
        x='Time',
        y='Activity',
        title=title
    )
    
    st.plotly_chart(fig, use_container_width=True)

