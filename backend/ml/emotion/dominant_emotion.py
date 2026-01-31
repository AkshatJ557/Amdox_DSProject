"""
Dominant emotion analysis module
"""
import sys
import os
from typing import Dict, List, Optional, Any
import base64
import numpy as np

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.ml.emotion.emotion_model import emotion_model


class DominantEmotionAnalyzer:
    """
    Analyzer for determining dominant emotion from frames
    """
    
    def __init__(self):
        self.model = emotion_model
    
    def analyze_frame(
        self, 
        frame_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a frame and detect dominant emotion
        
        Args:
            frame_data: Frame data containing image information
        
        Returns:
            dict: Analysis results including dominant emotion
        """
        try:
            # Extract image from frame data
            image = self._extract_image(frame_data)
            
            if image is None:
                return {
                    "success": False,
                    "error": "Could not extract image from frame data"
                }
            
            # Preprocess the image
            processed_image = self.model.preprocess_face(image)
            
            if processed_image.size == 0:
                return {
                    "success": False,
                    "error": "Failed to preprocess image"
                }
            
            # Detect emotion
            result = self.model.detect_emotion(processed_image)
            
            if result["success"]:
                dominant = result["dominant_emotion"]
                confidence = result["confidence"]
                
                # Calculate stress score based on emotion
                stress_score = self._emotion_to_stress(dominant)
                
                return {
                    "success": True,
                    "dominant_emotion": dominant,
                    "confidence": confidence,
                    "emotions": result["emotions"],
                    "stress_score": stress_score,
                    "timestamp": str(os.path.getctime(__file__))
                }
            
            return result
            
        except Exception as e:
            print(f"❌ Error analyzing frame: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_image(self, frame_data: Dict) -> Optional[np.ndarray]:
        """
        Extract image array from frame data
        
        Args:
            frame_data: Frame data dictionary
        
        Returns:
            np.ndarray: Image array or None
        """
        try:
            import cv2
            
            # Check if base64 encoded
            if "frame_base64" in frame_data and frame_data["frame_base64"]:
                image_data = base64.b64decode(frame_data["frame_base64"])
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return image
            
            # Check if raw image bytes
            if "image_bytes" in frame_data and frame_data["image_bytes"]:
                nparr = np.frombuffer(frame_data["image_bytes"], np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return image
            
            # Check if already a numpy array (for direct testing)
            if "image" in frame_data and isinstance(frame_data["image"], np.ndarray):
                return frame_data["image"]
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting image: {e}")
            return None
    
    def _emotion_to_stress(self, emotion: str) -> int:
        """
        Convert emotion to stress score
        
        Args:
            emotion: Emotion label
        
        Returns:
            int: Stress score (0-10)
        """
        stress_mapping = {
            'Happy': 1,
            'Surprise': 3,
            'Neutral': 4,
            'Sad': 6,
            'Fear': 7,
            'Disgust': 8,
            'Angry': 8
        }
        return stress_mapping.get(emotion, 5)
    
    def analyze_multiple_frames(
        self, 
        frames: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze multiple frames and aggregate results
        
        Args:
            frames: List of frame data dictionaries
        
        Returns:
            dict: Aggregated analysis results
        """
        try:
            if not frames:
                return {
                    "success": False,
                    "error": "No frames provided"
                }
            
            results = []
            for frame_data in frames:
                result = self.analyze_frame(frame_data)
                if result["success"]:
                    results.append(result)
            
            if not results:
                return {
                    "success": False,
                    "error": "No successful frame analyses"
                }
            
            # Aggregate results
            from collections import Counter
            
            emotions = [r["dominant_emotion"] for r in results]
            confidences = [r["confidence"] for r in results]
            stress_scores = [r.get("stress_score", 0) for r in results]
            
            emotion_counter = Counter(emotions)
            dominant = emotion_counter.most_common(1)[0][0]
            
            return {
                "success": True,
                "frame_count": len(frames),
                "successful_analyses": len(results),
                "dominant_emotion": dominant,
                "emotion_distribution": dict(emotion_counter),
                "average_confidence": sum(confidences) / len(confidences),
                "average_stress_score": sum(stress_scores) / len(stress_scores),
                "timestamp": str(os.path.getctime(__file__))
            }
            
        except Exception as e:
            print(f"❌ Error analyzing multiple frames: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """Get information about the analyzer"""
        return {
            "model_loaded": self.model.loaded if self.model else False,
            "model_path": self.model.model_path if self.model else None,
            "emotion_labels": self.model.EMOTION_LABELS if self.model else []
        }


# Create global analyzer instance
dominant_emotion_analyzer = DominantEmotionAnalyzer()

