"""
Enhanced Emotion Detection Model for Amdox
Production-grade CNN model wrapper with optimized preprocessing and inference
"""
import sys
import os
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from pathlib import Path
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.config import EMOTION_LABELS


class EmotionModel:
    """
    Enhanced wrapper for FER2013 Mini-XCEPTION emotion detection model
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.loaded = False
        self.model_path = model_path
        self.EMOTION_LABELS = EMOTION_LABELS
        
        # Model configuration
        self.input_shape = (64, 64, 1)  # Grayscale 64x64
        self.target_size = (64, 64)
        self.num_classes = len(EMOTION_LABELS)
        
        # Performance tracking
        self._inference_times = []
        self._prediction_count = 0
        
        # Confidence calibration
        self._confidence_threshold = 0.3  # Minimum confidence
        self._use_calibration = True
        
        logger.info("🧠 Emotion Model initialized")
        
        # Attempt to load model
        self._load_model()
    
    def _load_model(self):
        """Load the emotion detection model with error handling"""
        try:
            # Import TensorFlow/Keras
            import tensorflow as tf
            from tensorflow import keras
            
            # Suppress TF warnings
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
            tf.get_logger().setLevel('ERROR')
            
            # Determine model path
            if self.model_path is None:
                base_dir = Path(__file__).resolve().parent.parent.parent.parent
                self.model_path = str(base_dir / "models" / "fer2013_mini_XCEPTION.102-0.66.hdf5")
            
            # Check if model file exists
            if not os.path.exists(self.model_path):
                logger.warning(f"⚠️ Model file not found at {self.model_path}")
                logger.info("💡 Running in mock mode without actual emotion detection")
                self.loaded = False
                return
            
            logger.info(f"📥 Loading emotion model from: {self.model_path}")
            start_time = time.time()
            
            # Load the model
            self.model = keras.models.load_model(
                self.model_path,
                compile=False  # Faster loading
            )
            
            # Compile for inference optimization
            self.model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            load_time = time.time() - start_time
            
            self.loaded = True
            logger.info(f"✅ Emotion model loaded successfully in {load_time:.2f}s")
            logger.info(f"   Model: FER2013 Mini-XCEPTION")
            logger.info(f"   Input shape: {self.input_shape}")
            logger.info(f"   Classes: {self.num_classes}")
            logger.info(f"   Emotions: {', '.join(self.EMOTION_LABELS)}")
            
            # Warm up the model
            self._warmup_model()
            
        except ImportError as e:
            logger.error(f"❌ TensorFlow/Keras not available: {e}")
            logger.info("💡 Install with: pip install tensorflow")
            self.loaded = False
        except Exception as e:
            logger.error(f"❌ Error loading emotion model: {e}")
            logger.info("💡 Running in mock mode without actual emotion detection")
            self.loaded = False
    
    def _warmup_model(self):
        """Warm up model with dummy prediction for faster first inference"""
        try:
            if self.model is None:
                return
            
            logger.info("🔥 Warming up model...")
            dummy_input = np.zeros((1, 64, 64, 1), dtype=np.float32)
            
            # Run prediction to initialize model
            _ = self.model.predict(dummy_input, verbose=0)
            
            logger.info("✅ Model warmed up")
            
        except Exception as e:
            logger.warning(f"⚠️ Model warmup failed: {e}")
    
    def detect_emotion(
        self, 
        face_image: np.ndarray,
        return_all_probabilities: bool = False
    ) -> Dict[str, Any]:
        """
        Detect emotion from a preprocessed face image
        
        Args:
            face_image: Preprocessed face image array (64, 64, 1)
            return_all_probabilities: Return probabilities for all emotions
        
        Returns:
            dict: Emotion detection results with confidence
        """
        if not self.loaded or self.model is None:
            return self._mock_detection()
        
        try:
            start_time = time.time()
            
            # Validate input shape
            if len(face_image.shape) == 3:
                face_image = np.expand_dims(face_image, axis=0)
            
            if face_image.shape[1:] != self.input_shape:
                logger.warning(f"⚠️ Input shape {face_image.shape} != expected {self.input_shape}")
                return {
                    "success": False,
                    "error": f"Invalid input shape. Expected {self.input_shape}"
                }
            
            # Make prediction
            predictions = self.model.predict(face_image, verbose=0)
            
            # Track inference time
            inference_time = time.time() - start_time
            self._inference_times.append(inference_time)
            self._prediction_count += 1
            
            # Get results
            emotion_probs = predictions[0]
            
            # Apply calibration if enabled
            if self._use_calibration:
                emotion_probs = self._calibrate_confidence(emotion_probs)
            
            emotion_idx = np.argmax(emotion_probs)
            confidence = float(emotion_probs[emotion_idx])
            dominant_emotion = self.EMOTION_LABELS[emotion_idx]
            
            # Check confidence threshold
            if confidence < self._confidence_threshold:
                logger.warning(f"⚠️ Low confidence: {confidence:.3f} for {dominant_emotion}")
            
            # Create emotion dictionary
            emotions = {
                self.EMOTION_LABELS[i]: float(emotion_probs[i])
                for i in range(len(self.EMOTION_LABELS))
            }
            
            result = {
                "success": True,
                "dominant_emotion": dominant_emotion,
                "confidence": confidence,
                "emotions": emotions,
                "inference_time_ms": round(inference_time * 1000, 2)
            }
            
            # Add all probabilities if requested
            if return_all_probabilities:
                result["all_probabilities"] = emotion_probs.tolist()
            
            # Add quality indicators
            result["quality"] = self._assess_prediction_quality(confidence, emotion_probs)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error detecting emotion: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def detect_emotions_batch(
        self, 
        face_images: List[np.ndarray]
    ) -> List[Dict[str, Any]]:
        """
        Detect emotions for multiple faces in batch (more efficient)
        
        Args:
            face_images: List of preprocessed face images
        
        Returns:
            list: Detection results for each face
        """
        if not self.loaded or self.model is None:
            return [self._mock_detection() for _ in face_images]
        
        try:
            if not face_images:
                return []
            
            # Stack images into batch
            batch = np.stack(face_images, axis=0)
            
            start_time = time.time()
            
            # Batch prediction
            predictions = self.model.predict(batch, verbose=0)
            
            inference_time = time.time() - start_time
            per_image_time = inference_time / len(face_images)
            
            results = []
            for i, emotion_probs in enumerate(predictions):
                # Apply calibration
                if self._use_calibration:
                    emotion_probs = self._calibrate_confidence(emotion_probs)
                
                emotion_idx = np.argmax(emotion_probs)
                confidence = float(emotion_probs[emotion_idx])
                dominant_emotion = self.EMOTION_LABELS[emotion_idx]
                
                emotions = {
                    self.EMOTION_LABELS[j]: float(emotion_probs[j])
                    for j in range(len(self.EMOTION_LABELS))
                }
                
                results.append({
                    "success": True,
                    "dominant_emotion": dominant_emotion,
                    "confidence": confidence,
                    "emotions": emotions,
                    "inference_time_ms": round(per_image_time * 1000, 2)
                })
            
            self._prediction_count += len(face_images)
            logger.info(f"✅ Batch prediction: {len(face_images)} faces in {inference_time:.3f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in batch detection: {e}")
            return [{"success": False, "error": str(e)} for _ in face_images]
    
    def _mock_detection(self) -> Dict[str, Any]:
        """Return mock detection when model not available"""
        import random
        
        # Generate realistic mock data
        emotions = {label: round(random.random() * 0.2, 4) for label in self.EMOTION_LABELS}
        
        # Make one emotion dominant
        dominant = random.choice(self.EMOTION_LABELS)
        emotions[dominant] = round(0.6 + random.random() * 0.4, 4)
        
        return {
            "success": True,
            "dominant_emotion": dominant,
            "confidence": emotions[dominant],
            "emotions": emotions,
            "mock": True,
            "warning": "Model not loaded - using mock data"
        }
    
    def preprocess_face(
        self, 
        face_image: np.ndarray, 
        target_size: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """
        Preprocess a face image for emotion detection with enhancements
        
        Args:
            face_image: Raw face image (RGB or Grayscale)
            target_size: Target size (default: 64x64)
        
        Returns:
            np.ndarray: Preprocessed image ready for model
        """
        try:
            import cv2
            
            if target_size is None:
                target_size = self.target_size
            
            # Handle empty input
            if face_image is None or face_image.size == 0:
                logger.error("❌ Empty face image provided")
                return np.array([])
            
            # Resize to target size
            resized = cv2.resize(face_image, target_size, interpolation=cv2.INTER_AREA)
            
            # Convert to grayscale if needed
            if len(resized.shape) == 3 and resized.shape[2] == 3:
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            elif len(resized.shape) == 3 and resized.shape[2] == 4:
                gray = cv2.cvtColor(resized, cv2.COLOR_BGRA2GRAY)
            else:
                gray = resized
            
            # Apply histogram equalization for better contrast
            gray = cv2.equalizeHist(gray)
            
            # Normalize to [0, 1]
            normalized = gray.astype('float32') / 255.0
            
            # Add channel dimension
            processed = np.expand_dims(normalized, axis=-1)
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Error preprocessing face: {e}")
            return np.array([])
    
    def preprocess_face_with_detection(
        self,
        image: np.ndarray,
        detect_face: bool = True
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Preprocess image with optional face detection
        
        Args:
            image: Input image
            detect_face: Whether to detect face first
        
        Returns:
            tuple: (Preprocessed face, detection info)
        """
        try:
            import cv2
            
            info = {
                "face_detected": False,
                "face_location": None,
                "preprocessing_success": False
            }
            
            if detect_face:
                # Load face cascade
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
                
                # Convert to grayscale for detection
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # Detect faces
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                if len(faces) == 0:
                    logger.warning("⚠️ No face detected in image")
                    return None, info
                
                # Use the largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                
                info["face_detected"] = True
                info["face_location"] = {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
                
                # Extract face region
                face_region = gray[y:y+h, x:x+w]
            else:
                face_region = image
            
            # Preprocess
            processed = self.preprocess_face(face_region)
            
            if processed.size > 0:
                info["preprocessing_success"] = True
                return processed, info
            else:
                return None, info
            
        except Exception as e:
            logger.error(f"❌ Error in preprocessing with detection: {e}")
            return None, {"error": str(e)}
    
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
            
            if processed.size == 0:
                return {
                    "success": False,
                    "error": "Failed to preprocess image"
                }
            
            result = self.detect_emotion(processed)
            
            if result["success"]:
                result["processed_image_shape"] = processed.shape
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in detect_and_preprocess: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calibrate_confidence(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Calibrate confidence scores for better reliability
        
        Args:
            probabilities: Raw model probabilities
        
        Returns:
            np.ndarray: Calibrated probabilities
        """
        try:
            # Temperature scaling (T=1.5 works well for this model)
            temperature = 1.5
            calibrated = np.exp(np.log(probabilities + 1e-10) / temperature)
            calibrated = calibrated / np.sum(calibrated)
            
            return calibrated
            
        except Exception:
            return probabilities
    
    def _assess_prediction_quality(
        self, 
        confidence: float,
        probabilities: np.ndarray
    ) -> str:
        """
        Assess prediction quality based on confidence and distribution
        
        Args:
            confidence: Prediction confidence
            probabilities: All class probabilities
        
        Returns:
            str: Quality rating (excellent/good/fair/poor)
        """
        try:
            # Calculate entropy
            entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
            
            # Normalize entropy (max entropy for 7 classes is log(7))
            max_entropy = np.log(7)
            normalized_entropy = entropy / max_entropy
            
            # Quality assessment
            if confidence >= 0.8 and normalized_entropy < 0.4:
                return "excellent"
            elif confidence >= 0.6 and normalized_entropy < 0.6:
                return "good"
            elif confidence >= 0.4:
                return "fair"
            else:
                return "poor"
                
        except Exception:
            return "unknown"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the model"""
        info = {
            "loaded": self.loaded,
            "model_path": self.model_path,
            "emotion_labels": self.EMOTION_LABELS,
            "num_classes": self.num_classes,
            "input_shape": self.input_shape,
            "target_size": self.target_size,
            "prediction_count": self._prediction_count
        }
        
        if self.model:
            try:
                info["model_architecture"] = {
                    "input_shape": list(self.model.input.shape),
                    "output_shape": list(self.model.output.shape),
                    "total_params": int(self.model.count_params()),
                    "layers": len(self.model.layers)
                }
            except Exception:
                pass
        
        # Performance statistics
        if self._inference_times:
            info["performance"] = {
                "avg_inference_ms": round(np.mean(self._inference_times) * 1000, 2),
                "min_inference_ms": round(np.min(self._inference_times) * 1000, 2),
                "max_inference_ms": round(np.max(self._inference_times) * 1000, 2),
                "total_predictions": self._prediction_count
            }
        
        return info
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics"""
        if not self._inference_times:
            return {
                "message": "No predictions made yet"
            }
        
        times_ms = np.array(self._inference_times) * 1000
        
        return {
            "total_predictions": self._prediction_count,
            "avg_inference_ms": round(np.mean(times_ms), 2),
            "median_inference_ms": round(np.median(times_ms), 2),
            "std_inference_ms": round(np.std(times_ms), 2),
            "min_inference_ms": round(np.min(times_ms), 2),
            "max_inference_ms": round(np.max(times_ms), 2),
            "p95_inference_ms": round(np.percentile(times_ms, 95), 2),
            "p99_inference_ms": round(np.percentile(times_ms, 99), 2)
        }
    
    def reset_performance_stats(self):
        """Reset performance tracking"""
        self._inference_times = []
        self._prediction_count = 0
        logger.info("📊 Performance stats reset")
    
    def set_confidence_threshold(self, threshold: float):
        """
        Set minimum confidence threshold
        
        Args:
            threshold: Minimum confidence (0-1)
        """
        if 0 <= threshold <= 1:
            self._confidence_threshold = threshold
            logger.info(f"✅ Confidence threshold set to {threshold}")
        else:
            logger.error("❌ Threshold must be between 0 and 1")
    
    def enable_calibration(self, enable: bool = True):
        """
        Enable/disable confidence calibration
        
        Args:
            enable: Whether to enable calibration
        """
        self._use_calibration = enable
        logger.info(f"✅ Confidence calibration {'enabled' if enable else 'disabled'}")


# Create global model instance
emotion_model = EmotionModel()