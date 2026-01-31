"""
Form components for user input
"""
import streamlit as st


def stress_input_form() -> int:
    """
    Display stress level input form
    
    Returns:
        int: Selected stress level
    """
    st.markdown("### 😰 Stress Assessment")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stress_level = st.slider(
            "How stressed are you feeling right now?",
            min_value=1,
            max_value=10,
            value=5,
            help="1 = Not stressed at all, 10 = Extremely stressed"
        )
    
    with col2:
        # Display stress indicator
        if stress_level <= 3:
            st.success("🟢 Low stress")
        elif stress_level <= 6:
            st.warning("🟡 Moderate stress")
        else:
            st.error("🔴 High stress")
    
    # Show description
    stress_descriptions = {
        1: "Completely relaxed and calm",
        2: "Slightly tense but manageable",
        3: "Mild stress, feeling pressured",
        4: "Noticeable stress, still coping",
        5: "Moderate stress, somewhat overwhelmed",
        6: "High stress, difficulty concentrating",
        7: "Very stressed, needing relief",
        8: "Extremely stressed, nearly overwhelmed",
        9: "Severely stressed, very difficult to cope",
        10: "Maximum stress, cannot function normally"
    }
    
    st.info(f"**Current level:** {stress_descriptions.get(stress_level, 'Unknown')}")
    
    return stress_level


def recommendation_request_form() -> dict:
    """
    Display recommendation request form
    
    Returns:
        dict: Form data
    """
    st.markdown("### 💡 Get Personalized Recommendation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        emotion = st.selectbox(
            "What's your current emotion?",
            ['Happy', 'Neutral', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust'],
            index=0
        )
    
    with col2:
        stress_score = st.slider(
            "Stress level (1-10)",
            min_value=1,
            max_value=10,
            value=5
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        workload = st.select_slider(
            "Current workload",
            options=['Very Light', 'Light', 'Moderate', 'Heavy', 'Very Heavy'],
            value='Moderate'
        )
    
    with col4:
        deadline = st.select_slider(
            "Deadline pressure",
            options=['None', 'Low', 'Moderate', 'High', 'Very High'],
            value='Low'
        )
    
    col5, col6 = st.columns(2)
    
    with col5:
        sleep_hours = st.number_input(
            "Hours of sleep last night",
            min_value=0,
            max_value=24,
            value=7
        )
    
    with col6:
        submit = st.form_submit_button("Get Recommendation")
    
    if submit:
        return {
            'emotion': emotion,
            'stress_score': stress_score,
            'workload': workload,
            'deadline_pressure': deadline,
            'sleep_hours': sleep_hours,
            'submitted': True
        }
    
    return {'submitted': False}


def feedback_form() -> dict:
    """
    Display feedback form
    
    Returns:
        dict: Feedback data
    """
    st.markdown("### 📝 Feedback")
    
    with st.form("feedback_form"):
        helpful = st.radio(
            "Was this recommendation helpful?",
            ['Very Helpful', 'Somewhat Helpful', 'Not Helpful']
        )
        
        accuracy = st.slider(
            "How accurate was the emotion detection?",
            1, 10, 7
        )
        
        comments = st.text_area(
            "Additional comments (optional)",
            placeholder="Tell us how we can improve..."
        )
        
        submit = st.form_submit_button("Submit Feedback")
        
        if submit:
            return {
                'helpful': helpful,
                'accuracy': accuracy,
                'comments': comments,
                'submitted': True
            }
    
    return {'submitted': False}


def settings_form() -> dict:
    """
    Display settings form
    
    Returns:
        dict: Updated settings
    """
    st.markdown("### ⚙️ Settings")
    
    with st.form("settings_form"):
        notifications = st.checkbox(
            "Enable notifications",
            value=True
        )
        
        dark_mode = st.checkbox(
            "Dark mode",
            value=False
        )
        
        auto_detect = st.checkbox(
            "Auto-detect emotion on page load",
            value=True
        )
        
        sensitivity = st.select_slider(
            "Detection sensitivity",
            options=['Low', 'Medium', 'High'],
            value='Medium'
        )
        
        submit = st.form_submit_button("Save Settings")
        
        if submit:
            return {
                'notifications': notifications,
                'dark_mode': dark_mode,
                'auto_detect': auto_detect,
                'sensitivity': sensitivity,
                'submitted': True
            }
    
    return {'submitted': False}

