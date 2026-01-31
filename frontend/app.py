"""
Amdox Frontend Application
Main entry point for the Streamlit frontend
"""
import streamlit as st
import os
import sys

# Add parent directories to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Configure page
st.set_page_config(
    page_title="Amdox - Emotion Detection System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #fafafa;
    }
    .stButton > button {
        width: 100%;
    }
    .success-message {
        padding: 10px;
        border-radius: 5px;
        background-color: #d4edda;
        color: #155724;
    }
    .warning-message {
        padding: 10px;
        border-radius: 5px;
        background-color: #fff3cd;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point"""
    
    # Title and description
    st.title("🧠 Amdox")
    st.markdown("### Emotion Detection & Wellness Assistant")
    
    st.markdown("""
    Welcome to Amdox - an AI-powered emotion detection system that helps you:
    
    - 🎭 **Detect Emotions** - Real-time emotion recognition using AI
    - 📊 **Track Wellness** - Monitor your emotional well-being over time
    - 💡 **Get Recommendations** - Personalized suggestions based on your emotional state
    - 📈 **Analytics** - View detailed reports and trends
    """)
    
    # Quick start options
    st.markdown("## 🚀 Quick Start")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        ### 👤 Employee Login
        Access your personal dashboard with emotion tracking and recommendations.
        """)
        if st.button("Employee Login"):
            st.switch_page("frontend.pages.login")
    
    with col2:
        st.info("""
        ### 📊 HR Dashboard
        View team analytics and aggregate wellness reports.
        """)
        if st.button("HR Dashboard"):
            st.switch_page("frontend.pages.hr_dashboard")
    
    with col3:
        st.info("""
        ### 📝 Demo Mode
        Try out the emotion detection without logging in.
        """)
        if st.button("Try Demo"):
            st.session_state.demo_mode = True
            st.rerun()
    
    # Demo mode
    if st.session_state.get('demo_mode', False):
        show_demo_mode()
    
    # Features section
    st.markdown("## ✨ Features")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 🎭 Emotion Detection
        Uses advanced AI to detect emotions from facial expressions in real-time.
        """)
    
    with col2:
        st.markdown("""
        ### 📈 Stress Tracking
        Monitor your stress levels and identify patterns over time.
        """)
    
    with col3:
        st.markdown("""
        ### 💡 Smart Recommendations
        Get personalized task suggestions based on your emotional state.
        """)
    
    with col4:
        st.markdown("""
        ### 🔒 Privacy First
        Your data is encrypted and never shared with third parties.
        """)


def show_demo_mode():
    """Show demo mode interface"""
    st.markdown("---")
    st.subheader("🎮 Demo Mode")
    
    st.info("Try out the emotion detection without any login!")
    
    # Simple emotion detection demo
    st.markdown("### 📸 Quick Emotion Check")
    
    # Placeholder for camera
    st.warning("Camera input would appear here in demo mode")
    st.caption("In a real deployment, you can take a photo and get instant emotion analysis")
    
    # Show sample emotions
    st.markdown("### 🎭 Sample Emotions")
    
    import random
    emotions = ['Happy 😊', 'Neutral 😐', 'Sad 😢', 'Angry 😠']
    selected = st.selectbox("Select an emotion to see sample recommendation:", emotions)
    
    st.success(f"Recommendation for {selected}: Take a short break and continue with your great work!")
    
    if st.button("Exit Demo Mode"):
        st.session_state.demo_mode = False
        st.rerun()


# Session state initialization
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False


if __name__ == "__main__":
    main()

