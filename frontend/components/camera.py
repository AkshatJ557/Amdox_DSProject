"""
Camera input component for emotion detection
"""
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# Add parent directory to path
import sys
import os
frontend_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(frontend_dir)
root_dir = os.path.dirname(app_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


def capture_image() -> np.ndarray:
    """
    Capture image from camera
    
    Returns:
        np.ndarray: Captured image
    """
    try:
        # Use Streamlit's camera input widget
        img_file = st.camera_input("Take a photo for emotion detection")
        
        if img_file is not None:
            # Convert to numpy array
            bytes_data = img_file.getvalue()
            cv2_img = cv2.imdecode(
                np.frombuffer(bytes_data, np.uint8), 
                cv2.IMREAD_COLOR
            )
            return cv2_img
        return None
        
    except Exception as e:
        st.error(f"Error capturing image: {e}")
        return None


def display_camera_feed() -> bool:
    """
    Display camera feed and check availability
    
    Returns:
        bool: True if camera is available
    """
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.warning("Could not access camera. Please check camera permissions.")
            return False
        
        # Release camera immediately after check
        cap.release()
        
        return True
        
    except Exception as e:
        st.error(f"Error accessing camera: {e}")
        return False


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for emotion detection
    
    Args:
        image: Input image as numpy array
    
    Returns:
        np.ndarray: Preprocessed image
    """
    try:
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to 64x64 for the model
        resized = cv2.resize(image, (64, 64))
        
        # Convert to grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        
        # Normalize
        normalized = gray.astype('float32') / 255.0
        
        return normalized
        
    except Exception as e:
        st.error(f"Error preprocessing image: {e}")
        return np.ndarray()


def image_to_base64(image: np.ndarray) -> str:
    """
    Convert numpy array image to base64 string
    
    Args:
        image: Input image as numpy array
    
    Returns:
        str: Base64 encoded image
    """
    try:
        # Convert to PIL Image
        if len(image.shape) == 2:
            pil_img = Image.fromarray(image)
        else:
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Save to buffer
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG")
        
        # Encode to base64
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error converting image: {e}")
        return ""


def display_emotion_result(emotion: str, confidence: float):
    """
    Display emotion detection result
    
    Args:
        emotion: Detected emotion
        confidence: Detection confidence
    """
    # Create emoji mapping
    emoji_map = {
        'Happy': '😊',
        'Sad': '😢',
        'Angry': '😠',
        'Fear': '😨',
        'Surprise': '😮',
        'Neutral': '😐',
        'Disgust': '🤢'
    }
    
    emoji = emoji_map.get(emotion, '😐')
    
    st.success(f"Detected: {emotion} {emoji}")
    st.progress(int(confidence * 100))
    st.caption(f"Confidence: {confidence:.2%}")


def emotion_camera_input() -> tuple:
    """
    Camera input component for emotion detection
    
    Returns:
        tuple: (image_array, captured_flag)
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        img_file = st.camera_input(
            "📸 Click to capture your emotion", 
            key="emotion_camera"
        )
    
    with col2:
        st.write("### Instructions")
        st.info("""
        1. Ensure good lighting
        2. Face the camera directly
        3. Remove any face coverings
        4. Stay still during capture
        """)
    
    if img_file is not None:
        bytes_data = img_file.getvalue()
        cv2_img = cv2.imdecode(
            np.frombuffer(bytes_data, np.uint8), 
            cv2.IMREAD_COLOR
        )
        return cv2_img, True
    
    return None, False

