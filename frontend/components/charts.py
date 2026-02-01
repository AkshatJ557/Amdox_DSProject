"""
Enhanced Charts Component for Amdox
Interactive data visualizations using Plotly
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

# Color schemes aligned with backend zones
ZONE_COLORS = {
    'GREEN': '#4CAF50',
    'YELLOW': '#FFC107',
    'ORANGE': '#FF9800',
    'RED': '#F44336'
}

EMOTION_COLORS = {
    'Happy': '#4CAF50',
    'Surprise': '#FFC107',
    'Neutral': '#9E9E9E',
    'Sad': '#FF9800',
    'Fear': '#FF9800',
    'Disgust': '#F44336',
    'Angry': '#F44336'
}

STRESS_COLOR_SCALE = [
    [0, '#4CAF50'],      # Green (0-3)
    [0.3, '#FFC107'],    # Yellow (3-5)
    [0.6, '#FF9800'],    # Orange (5-7)
    [1, '#F44336']       # Red (7-10)
]


def create_emotion_pie_chart(emotion_distribution: Dict[str, int]) -> go.Figure:
    """
    Create emotion distribution pie chart
    
    Args:
        emotion_distribution: Dict of emotion counts
    
    Returns:
        Plotly figure
    """
    if not emotion_distribution:
        fig = go.Figure()
        fig.add_annotation(
            text="No emotion data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    emotions = list(emotion_distribution.keys())
    counts = list(emotion_distribution.values())
    colors = [EMOTION_COLORS.get(e, '#9E9E9E') for e in emotions]
    
    fig = go.Figure(data=[go.Pie(
        labels=emotions,
        values=counts,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        hovertemplate="<b>%{label}</b><br>" +
                      "Count: %{value}<br>" +
                      "Percentage: %{percent}<br>" +
                      "<extra></extra>"
    )])
    
    fig.update_layout(
        title={
            'text': "Emotion Distribution",
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        height=400,
        margin=dict(t=80, b=40, l=40, r=40)
    )
    
    return fig


def create_stress_trend_chart(
    stress_data: List[Dict],
    time_field: str = 'timestamp',
    stress_field: str = 'stress_score'
) -> go.Figure:
    """
    Create stress trend line chart
    
    Args:
        stress_data: List of stress data points
        time_field: Name of timestamp field
        stress_field: Name of stress score field
    
    Returns:
        Plotly figure
    """
    if not stress_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No stress data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    df = pd.DataFrame(stress_data)
    
    # Ensure timestamp is datetime
    if time_field in df.columns:
        df[time_field] = pd.to_datetime(df[time_field])
    
    # Sort by time
    df = df.sort_values(time_field)
    
    fig = go.Figure()
    
    # Add stress line
    fig.add_trace(go.Scatter(
        x=df[time_field],
        y=df[stress_field],
        mode='lines+markers',
        name='Stress Level',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>" +
                      "Stress: %{y}/10<br>" +
                      "<extra></extra>"
    ))
    
    # Add threshold lines
    fig.add_hline(
        y=7, line_dash="dash", line_color="#F44336",
        annotation_text="High Stress", annotation_position="right"
    )
    fig.add_hline(
        y=3, line_dash="dash", line_color="#FFC107",
        annotation_text="Moderate", annotation_position="right"
    )
    
    # Add colored zones
    fig.add_hrect(y0=0, y1=3, fillcolor="#4CAF50", opacity=0.1, line_width=0)
    fig.add_hrect(y0=3, y1=7, fillcolor="#FFC107", opacity=0.1, line_width=0)
    fig.add_hrect(y0=7, y1=10, fillcolor="#F44336", opacity=0.1, line_width=0)
    
    fig.update_layout(
        title={
            'text': "Stress Trend Over Time",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Time",
        yaxis_title="Stress Score (0-10)",
        yaxis=dict(range=[0, 10]),
        hovermode='x unified',
        height=400,
        margin=dict(t=80, b=60, l=60, r=100)
    )
    
    return fig


def create_emotion_timeline(emotion_data: List[Dict]) -> go.Figure:
    """
    Create emotion timeline with colors
    
    Args:
        emotion_data: List of emotion data points
    
    Returns:
        Plotly figure
    """
    if not emotion_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No emotion timeline data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    df = pd.DataFrame(emotion_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Map emotions to colors
    df['color'] = df['emotion'].map(EMOTION_COLORS)
    
    fig = go.Figure()
    
    # Add scatter plot with emotion colors
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['emotion'],
        mode='markers',
        marker=dict(
            size=15,
            color=df['color'],
            line=dict(width=2, color='white')
        ),
        text=df['emotion'],
        hovertemplate="<b>%{text}</b><br>" +
                      "Time: %{x}<br>" +
                      "<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            'text': "Emotion Timeline",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Time",
        yaxis_title="Emotion",
        height=400,
        margin=dict(t=80, b=60, l=100, r=60)
    )
    
    return fig


def create_stress_gauge(stress_score: float) -> go.Figure:
    """
    Create stress gauge meter
    
    Args:
        stress_score: Current stress score (0-10)
    
    Returns:
        Plotly figure
    """
    # Determine color based on score
    if stress_score < 3:
        color = "#4CAF50"
        level = "Low"
    elif stress_score < 7:
        color = "#FFC107"
        level = "Moderate"
    else:
        color = "#F44336"
        level = "High"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=stress_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>Stress Level: {level}</b>"},
        delta={'reference': 5, 'increasing': {'color': "#F44336"}},
        gauge={
            'axis': {'range': [None, 10], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 3], 'color': "#E8F5E9"},
                {'range': [3, 7], 'color': "#FFF9C4"},
                {'range': [7, 10], 'color': "#FFEBEE"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 7
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(t=60, b=20, l=20, r=20)
    )
    
    return fig


def create_emotion_bar_chart(emotion_distribution: Dict[str, int]) -> go.Figure:
    """
    Create horizontal bar chart for emotions
    
    Args:
        emotion_distribution: Dict of emotion counts
    
    Returns:
        Plotly figure
    """
    if not emotion_distribution:
        fig = go.Figure()
        fig.add_annotation(
            text="No emotion data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Sort by count
    sorted_emotions = sorted(emotion_distribution.items(), key=lambda x: x[1], reverse=True)
    emotions = [e[0] for e in sorted_emotions]
    counts = [e[1] for e in sorted_emotions]
    colors = [EMOTION_COLORS.get(e, '#9E9E9E') for e in emotions]
    
    fig = go.Figure(go.Bar(
        x=counts,
        y=emotions,
        orientation='h',
        marker=dict(color=colors),
        text=counts,
        textposition='auto',
        hovertemplate="<b>%{y}</b><br>" +
                      "Count: %{x}<br>" +
                      "<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            'text': "Emotion Frequency",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Count",
        yaxis_title="Emotion",
        height=400,
        margin=dict(t=80, b=60, l=100, r=60)
    )
    
    return fig


def create_heatmap(data: pd.DataFrame, x_col: str, y_col: str, value_col: str) -> go.Figure:
    """
    Create heatmap visualization
    
    Args:
        data: DataFrame with data
        x_col: X-axis column name
        y_col: Y-axis column name
        value_col: Value column name
    
    Returns:
        Plotly figure
    """
    pivot_table = data.pivot_table(
        values=value_col,
        index=y_col,
        columns=x_col,
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale='RdYlGn_r',
        hovertemplate="<b>%{y}</b><br>" +
                      "%{x}<br>" +
                      "Value: %{z:.2f}<br>" +
                      "<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            'text': "Activity Heatmap",
            'x': 0.5,
            'xanchor': 'center'
        },
        height=400,
        margin=dict(t=80, b=60, l=100, r=60)
    )
    
    return fig


def create_multi_line_chart(
    data: Dict[str, List[Dict]],
    time_field: str = 'timestamp',
    value_field: str = 'value'
) -> go.Figure:
    """
    Create multi-line comparison chart
    
    Args:
        data: Dict of series name -> data points
        time_field: Timestamp field name
        value_field: Value field name
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    for series_name, series_data in data.items():
        if series_data:
            df = pd.DataFrame(series_data)
            df[time_field] = pd.to_datetime(df[time_field])
            df = df.sort_values(time_field)
            
            fig.add_trace(go.Scatter(
                x=df[time_field],
                y=df[value_field],
                mode='lines+markers',
                name=series_name,
                hovertemplate="<b>" + series_name + "</b><br>" +
                              "Time: %{x}<br>" +
                              "Value: %{y}<br>" +
                              "<extra></extra>"
            ))
    
    fig.update_layout(
        title={
            'text': "Multi-Series Comparison",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Time",
        yaxis_title="Value",
        hovermode='x unified',
        height=400,
        margin=dict(t=80, b=60, l=60, r=60)
    )
    
    return fig


def create_box_plot(data: List[Dict], category_field: str, value_field: str) -> go.Figure:
    """
    Create box plot for distribution analysis
    
    Args:
        data: List of data points
        category_field: Category field name
        value_field: Value field name
    
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    categories = df[category_field].unique()
    
    for category in categories:
        category_data = df[df[category_field] == category][value_field]
        color = EMOTION_COLORS.get(category, '#9E9E9E')
        
        fig.add_trace(go.Box(
            y=category_data,
            name=category,
            marker_color=color,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title={
            'text': "Distribution Analysis",
            'x': 0.5,
            'xanchor': 'center'
        },
        yaxis_title="Value",
        height=400,
        margin=dict(t=80, b=60, l=60, r=60)
    )
    
    return fig


def render_dashboard_metrics(metrics: Dict[str, Any]):
    """
    Render key metrics in a dashboard layout
    
    Args:
        metrics: Dictionary of metric values
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Users",
            metrics.get('total_users', 0),
            delta=metrics.get('new_users', 0)
        )
    
    with col2:
        st.metric(
            "Avg Stress",
            f"{metrics.get('avg_stress', 0):.1f}/10",
            delta=f"{metrics.get('stress_change', 0):.1f}"
        )
    
    with col3:
        st.metric(
            "Active Sessions",
            metrics.get('active_sessions', 0)
        )
    
    with col4:
        wellness_score = metrics.get('wellness_score', 0)
        st.metric(
            "Wellness Score",
            f"{wellness_score}/100",
            delta=metrics.get('wellness_change', 0)
        )


def create_team_comparison_chart(team_data: Dict[str, Dict]) -> go.Figure:
    """
    Create team comparison bar chart
    
    Args:
        team_data: Dict of team_id -> metrics
    
    Returns:
        Plotly figure
    """
    teams = list(team_data.keys())
    avg_stress = [team_data[t].get('avg_stress', 0) for t in teams]
    
    colors = ['#F44336' if s >= 7 else '#FFC107' if s >= 3 else '#4CAF50' for s in avg_stress]
    
    fig = go.Figure(go.Bar(
        x=teams,
        y=avg_stress,
        marker=dict(color=colors),
        text=[f"{s:.1f}" for s in avg_stress],
        textposition='auto',
        hovertemplate="<b>%{x}</b><br>" +
                      "Avg Stress: %{y:.1f}/10<br>" +
                      "<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            'text': "Team Stress Comparison",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Team",
        yaxis_title="Average Stress (0-10)",
        yaxis=dict(range=[0, 10]),
        height=400,
        margin=dict(t=80, b=60, l=60, r=60)
    )
    
    return fig

if __name__ == "__main__":
    # For testing
    st.title("📊 Charts Component Demo")
    
    # Sample data
    sample_emotions = {
        'Happy': 45,
        'Neutral': 30,
        'Sad': 15,
        'Angry': 10
    }
    
    sample_stress = [
        {'timestamp': datetime.now() - timedelta(hours=i), 'stress_score': np.random.randint(0, 10)}
        for i in range(24, 0, -1)
    ]
    
    # Render charts
    st.plotly_chart(create_emotion_pie_chart(sample_emotions), use_container_width=True)
    st.plotly_chart(create_stress_trend_chart(sample_stress), use_container_width=True)
    st.plotly_chart(create_stress_gauge(6.5), use_container_width=True)