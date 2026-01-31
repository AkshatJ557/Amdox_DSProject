"""
Emotion detection model wrapper
"""
import sys
import os
from typing import Dict, List, Optional, Any
import numpy as np

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.config import EMOTION_LABELS


class EmotionModel:
    """
    Wrapper for the emotion detection model
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.loaded = False
        self.model_path = model_path
        self.EMOTION_LABELS = EMOTION_LABELS
        
        # Attempt to load model
        self._load_model()
    
    def _load_model(self):
        """Load the emotion detection model"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from pathlib import Path
            
            if self.model_path is None:
                base_dir = Path(__file__).resolve().parent.parent.parent
                self.model_path = str(base_dir / "models" / "fer2013_mini_XCEPTION.102-0.66.hdf5")
            
            # Check if model file exists
            if not os.path.exists(self.model_path):
                print(f"⚠️ Model file not found at {self.model_path}")
                print("💡 Running in mock mode without actual emotion detection")
                self.loaded = False
                return
            
            # Load the model
            self.model = keras.models.load_model(self.model_path)
            self.loaded = True
            print(f"✅ Emotion model loaded successfully from {self.model_path}")
            
        except Exception as e:
            print(f"❌ Error loading emotion model: {e}")
            print("💡 Running in mock mode without actual emotion detection")
            self.loaded = False
    
    def detect_emotion(self, face_image: np.ndarray) -> Dict[str, Any]:
        """
        Detect emotion from a face image
        
        Args:
            face_image: Preprocessed face image array
        
        Returns:
            dict: Emotion detection results
        """
        if not self.loaded or self.model is None:
            # Return mock data when model not loaded
            return self._mock_detection()
        
        try:
            # Ensure proper shape
            if len(face_image.shape) == 3:
                face_image = np.expand_dims(face_image, axis=0)
            
            # Make prediction
            predictions = self.model.predict(face_image, verbose=0)
            
            # Get results
            emotion_probs = predictions[0]
            emotion_idx = np.argmax(emotion_probs)
            confidence = float(emotion_probs[emotion_idx])
            
            # Create emotion dictionary
            emotions = {
                self.EMOTION_LABELS[i]: float(emotion_probs[i])
                for i in range(len(self.EMOTION_LABELS))
            }
            
            return {
                "success": True,
                "dominant_emotion": self.EMOTION_LABELS[emotion_idx],
                "confidence": confidence,
                "emotions": emotions
            }
            
        except Exception as e:
            print(f"❌ Error detecting emotion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _mock_detection(self) -> Dict[str, Any]:
        """Return mock detection when model not available"""
        import random
        
        emotions = {label: round(random.random() * 0.3, 4) for label in self.EMOTION_LABELS}
        # Make one emotion dominant
        dominant = random.choice(self.EMOTION_LABELS)
        emotions[dominant] = round(0.7 + random.random() * 0.3, 4)
        
        return {
            "success": True,
            "dominant_emotion": dominant,
            "confidence": emotions[dominant],
            "emotions": emotions,
            "mock": True
        }
    
    def preprocess_face(
        self, 
        face_image: np.ndarray, 
        target_size: tuple = (64, 64)
    ) -> np.ndarray:
        """
        Preprocess a face image for emotion detection
        
        Args:
            face_image: Raw face image
            target_size: Target size for the model
        
        Returns:
            np.ndarray: Preprocessed image
        """
        try:
            import cv2
            
            # Resize to target size
            resized = cv2.resize(face_image, target_size)
            
            # Convert to grayscale if needed
            if len(resized.shape) == 3 and resized.shape[2] == 3:
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            else:
                gray = resized
            
            # Normalize
            normalized = gray.astype('float32') / 255.0
            
            # Add batch and channel dimensions
            processed = np.expand_dims(np.expand_dims(normalized, axis=0), axis=-1)
            
            return processed
            
        except Exception as e:
            print(f"❌ Error preprocessing face: {e}")
            return np.ndarray()
    
    def detect_and_preprocess(
        self, 
        face_image: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detect emotion and return preprocessed result
        
        Args:
            face_image: Raw face image
        
        Returns:
            dict: Detection results with preprocessed data
        """
        try:
            processed = self.preprocess_face(face_image)
            result = self.detect_emotion(processed)
            
            if result["success"]:
                result["processed_image"] = processed
            
            return result
            
        except Exception as e:
            print(f"❌ Error in detect_and_preprocess: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "loaded": self.loaded,
            "model_path": self.model_path,
            "emotion_labels": self.EMOTION_LABELS,
            "input_shape": list(self.model.input.shape) if self.model else None,
            "output_shape": list(self.model.output.shape) if self.model else None
        }


# Create global model instance
emotion_model = EmotionModel()

