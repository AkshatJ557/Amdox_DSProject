"""
Enhanced Dominant Emotion Analyzer for Amdox
Production-grade emotion aggregation with temporal analysis and confidence weighting
"""
import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, deque
from datetime import datetime
import base64
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.ml.emotion.emotion_model import emotion_model


class DominantEmotionAnalyzer:
    """
    Enhanced analyzer for determining dominant emotion from multiple frames
    """
    
    def __init__(self):
        self.model = emotion_model
        
        # Analysis configuration
        self.use_confidence_weighting = True
        self.temporal_smoothing = True
        self.outlier_rejection = True
        
        # Smoothing window
        self.smoothing_window = 5
        self._recent_emotions = deque(maxlen=self.smoothing_window)
        
        # Performance tracking
        self._analysis_count = 0
        
        logger.info("🎯 Dominant Emotion Analyzer initialized")
    
    def analyze_frame(
        self, 
        frame_data: Dict[str, Any],
        apply_smoothing: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a frame and detect dominant emotion with enhancements
        
        Args:
            frame_data: Frame data containing image information
            apply_smoothing: Apply temporal smoothing
        
        Returns:
            dict: Analysis results including dominant emotion
        """
        try:
            # Extract and validate image
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
            result = self.model.detect_emotion(processed_image, return_all_probabilities=True)
            
            if not result.get("success"):
                return result
            
            dominant = result["dominant_emotion"]
            confidence = result["confidence"]
            
            # Apply temporal smoothing if enabled
            if apply_smoothing and self.temporal_smoothing:
                dominant, confidence = self._apply_temporal_smoothing(
                    dominant, 
                    confidence,
                    result["emotions"]
                )
                result["smoothed"] = True
                result["dominant_emotion"] = dominant
                result["confidence"] = confidence
            
            # Calculate stress score based on emotion
            stress_score = self._emotion_to_stress(dominant, confidence)
            result["stress_score"] = stress_score
            
            # Add quality assessment
            result["analysis_quality"] = self._assess_analysis_quality(result)
            
            # Track analysis
            self._analysis_count += 1
            result["timestamp"] = datetime.utcnow().isoformat()
            
            logger.debug(f"📸 Frame analyzed: {dominant} ({confidence:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing frame: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def analyze_multiple_frames(
        self, 
        frames: List[Dict[str, Any]],
        method: str = "confidence_weighted"
    ) -> Dict[str, Any]:
        """
        Analyze multiple frames and aggregate results with advanced methods
        
        Args:
            frames: List of frame data dictionaries
            method: Aggregation method (confidence_weighted/majority_vote/temporal)
        
        Returns:
            dict: Aggregated analysis results
        """
        try:
            if not frames:
                return {
                    "success": False,
                    "error": "No frames provided"
                }
            
            logger.info(f"🎬 Analyzing {len(frames)} frames with method: {method}")
            
            # Analyze each frame
            results = []
            for i, frame_data in enumerate(frames):
                result = self.analyze_frame(frame_data, apply_smoothing=False)
                if result.get("success"):
                    result["frame_index"] = i
                    results.append(result)
            
            if not results:
                return {
                    "success": False,
                    "error": "No successful frame analyses"
                }
            
            # Aggregate based on method
            if method == "confidence_weighted":
                aggregated = self._confidence_weighted_aggregation(results)
            elif method == "majority_vote":
                aggregated = self._majority_vote_aggregation(results)
            elif method == "temporal":
                aggregated = self._temporal_aggregation(results)
            else:
                logger.warning(f"⚠️ Unknown method {method}, using confidence_weighted")
                aggregated = self._confidence_weighted_aggregation(results)
            
            # Add comprehensive statistics
            aggregated.update({
                "frame_count": len(frames),
                "successful_analyses": len(results),
                "failed_analyses": len(frames) - len(results),
                "aggregation_method": method,
                "detailed_results": self._get_detailed_statistics(results)
            })
            
            return aggregated
            
        except Exception as e:
            logger.error(f"❌ Error analyzing multiple frames: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_session(
        self,
        frames: List[Dict[str, Any]],
        session_duration_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze a complete session with temporal context
        
        Args:
            frames: List of all session frames
            session_duration_seconds: Optional session duration
        
        Returns:
            dict: Comprehensive session analysis
        """
        try:
            if not frames:
                return {
                    "success": False,
                    "error": "No frames in session"
                }
            
            logger.info(f"📊 Analyzing session with {len(frames)} frames")
            
            # Analyze all frames
            base_result = self.analyze_multiple_frames(frames, method="confidence_weighted")
            
            if not base_result.get("success"):
                return base_result
            
            # Add session-specific analysis
            session_analysis = {
                **base_result,
                "session_analysis": {
                    "emotion_transitions": self._analyze_emotion_transitions(frames),
                    "stability_score": self._calculate_stability_score(base_result.get("detailed_results", {})),
                    "stress_progression": self._analyze_stress_progression(frames),
                    "peak_emotions": self._identify_peak_emotions(base_result.get("detailed_results", {}))
                }
            }
            
            if session_duration_seconds:
                session_analysis["session_duration_seconds"] = session_duration_seconds
                session_analysis["frames_per_second"] = round(len(frames) / session_duration_seconds, 2)
            
            return session_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_image(self, frame_data: Dict) -> Optional[np.ndarray]:
        """
        Extract image array from frame data with multiple format support
        
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
            
            # Check if already a numpy array
            if "image" in frame_data and isinstance(frame_data["image"], np.ndarray):
                return frame_data["image"]
            
            # Check if file path
            if "image_path" in frame_data and frame_data["image_path"]:
                if os.path.exists(frame_data["image_path"]):
                    image = cv2.imread(frame_data["image_path"])
                    return image
            
            logger.error("❌ No valid image data found in frame_data")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting image: {e}")
            return None
    
    def _emotion_to_stress(self, emotion: str, confidence: float) -> int:
        """
        Convert emotion to stress score with confidence adjustment
        
        Args:
            emotion: Emotion label
            confidence: Confidence score
        
        Returns:
            int: Stress score (0-10)
        """
        # Base stress mapping
        stress_mapping = {
            'Happy': 1,
            'Surprise': 3,
            'Neutral': 4,
            'Sad': 6,
            'Fear': 7,
            'Disgust': 8,
            'Angry': 8
        }
        
        base_stress = stress_mapping.get(emotion, 5)
        
        # Adjust based on confidence
        # High confidence in negative emotions → higher stress
        # Low confidence in negative emotions → lower adjustment
        if emotion in ['Sad', 'Fear', 'Disgust', 'Angry']:
            adjustment = (confidence - 0.5) * 2  # Range: -1 to +1
            adjusted_stress = base_stress + adjustment
        else:
            adjusted_stress = base_stress
        
        # Clamp to valid range
        return max(0, min(10, int(round(adjusted_stress))))
    
    def _apply_temporal_smoothing(
        self,
        current_emotion: str,
        current_confidence: float,
        all_emotions: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Apply temporal smoothing to reduce jitter
        
        Args:
            current_emotion: Current frame's emotion
            current_confidence: Current frame's confidence
            all_emotions: All emotion probabilities
        
        Returns:
            tuple: (smoothed_emotion, smoothed_confidence)
        """
        try:
            # Add current to history
            self._recent_emotions.append({
                "emotion": current_emotion,
                "confidence": current_confidence,
                "all_emotions": all_emotions
            })
            
            if len(self._recent_emotions) < 2:
                return current_emotion, current_confidence
            
            # Aggregate recent emotions with decay
            weighted_emotions = Counter()
            total_weight = 0
            
            for i, entry in enumerate(self._recent_emotions):
                # More recent frames get higher weight
                weight = (i + 1) / len(self._recent_emotions)
                weight *= entry["confidence"]  # Weight by confidence
                
                weighted_emotions[entry["emotion"]] += weight
                total_weight += weight
            
            # Get smoothed dominant emotion
            if total_weight > 0:
                smoothed_emotion = weighted_emotions.most_common(1)[0][0]
                smoothed_confidence = weighted_emotions[smoothed_emotion] / total_weight
                return smoothed_emotion, min(1.0, smoothed_confidence)
            
            return current_emotion, current_confidence
            
        except Exception as e:
            logger.error(f"Error in temporal smoothing: {e}")
            return current_emotion, current_confidence
    
    def _confidence_weighted_aggregation(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate using confidence-weighted voting"""
        try:
            emotion_scores = Counter()
            confidences = []
            stress_scores = []
            
            for result in results:
                emotion = result.get("dominant_emotion")
                confidence = result.get("confidence", 0)
                
                # Weight by confidence
                emotion_scores[emotion] += confidence
                confidences.append(confidence)
                stress_scores.append(result.get("stress_score", 0))
            
            # Get weighted dominant emotion
            dominant = emotion_scores.most_common(1)[0][0]
            total_weight = sum(emotion_scores.values())
            weighted_confidence = emotion_scores[dominant] / total_weight if total_weight > 0 else 0
            
            # Calculate average stress
            avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
            
            return {
                "success": True,
                "dominant_emotion": dominant,
                "confidence": round(weighted_confidence, 3),
                "average_stress_score": round(avg_stress, 2),
                "emotion_distribution": dict(emotion_scores)
            }
            
        except Exception as e:
            logger.error(f"Error in confidence weighted aggregation: {e}")
            return {"success": False, "error": str(e)}
    
    def _majority_vote_aggregation(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate using simple majority voting"""
        try:
            emotions = [r.get("dominant_emotion") for r in results]
            confidences = [r.get("confidence", 0) for r in results]
            stress_scores = [r.get("stress_score", 0) for r in results]
            
            emotion_counter = Counter(emotions)
            dominant = emotion_counter.most_common(1)[0][0]
            
            # Average confidence for dominant emotion
            dominant_confidences = [
                r.get("confidence", 0) for r in results 
                if r.get("dominant_emotion") == dominant
            ]
            avg_confidence = sum(dominant_confidences) / len(dominant_confidences)
            
            return {
                "success": True,
                "dominant_emotion": dominant,
                "confidence": round(avg_confidence, 3),
                "average_stress_score": round(sum(stress_scores) / len(stress_scores), 2),
                "emotion_distribution": dict(emotion_counter)
            }
            
        except Exception as e:
            logger.error(f"Error in majority vote aggregation: {e}")
            return {"success": False, "error": str(e)}
    
    def _temporal_aggregation(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate with temporal weighting (recent frames matter more)"""
        try:
            weighted_emotions = Counter()
            weighted_stress = 0
            total_weight = 0
            
            for i, result in enumerate(results):
                # Linear temporal weight (more recent = higher weight)
                weight = (i + 1) / len(results)
                weight *= result.get("confidence", 0)  # Also weight by confidence
                
                emotion = result.get("dominant_emotion")
                weighted_emotions[emotion] += weight
                weighted_stress += result.get("stress_score", 0) * weight
                total_weight += weight
            
            dominant = weighted_emotions.most_common(1)[0][0]
            weighted_confidence = weighted_emotions[dominant] / total_weight if total_weight > 0 else 0
            avg_stress = weighted_stress / total_weight if total_weight > 0 else 0
            
            return {
                "success": True,
                "dominant_emotion": dominant,
                "confidence": round(weighted_confidence, 3),
                "average_stress_score": round(avg_stress, 2),
                "emotion_distribution": dict(weighted_emotions)
            }
            
        except Exception as e:
            logger.error(f"Error in temporal aggregation: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_detailed_statistics(self, results: List[Dict]) -> Dict[str, Any]:
        """Get detailed statistics from analysis results"""
        try:
            emotions = [r.get("dominant_emotion") for r in results]
            confidences = [r.get("confidence", 0) for r in results]
            stress_scores = [r.get("stress_score", 0) for r in results]
            
            return {
                "emotion_counts": dict(Counter(emotions)),
                "confidence_stats": {
                    "mean": round(np.mean(confidences), 3),
                    "std": round(np.std(confidences), 3),
                    "min": round(np.min(confidences), 3),
                    "max": round(np.max(confidences), 3)
                },
                "stress_stats": {
                    "mean": round(np.mean(stress_scores), 2),
                    "std": round(np.std(stress_scores), 2),
                    "min": int(np.min(stress_scores)),
                    "max": int(np.max(stress_scores))
                }
            }
        except Exception:
            return {}
    
    def _analyze_emotion_transitions(self, frames: List[Dict]) -> Dict[str, Any]:
        """Analyze how emotions transition throughout session"""
        try:
            transitions = []
            prev_emotion = None
            
            for frame in frames:
                result = self.analyze_frame(frame, apply_smoothing=False)
                if result.get("success"):
                    current_emotion = result.get("dominant_emotion")
                    if prev_emotion and prev_emotion != current_emotion:
                        transitions.append({
                            "from": prev_emotion,
                            "to": current_emotion
                        })
                    prev_emotion = current_emotion
            
            # Count transition types
            transition_counts = Counter(
                f"{t['from']} → {t['to']}" for t in transitions
            )
            
            return {
                "total_transitions": len(transitions),
                "unique_transitions": len(transition_counts),
                "most_common_transitions": dict(transition_counts.most_common(5))
            }
            
        except Exception:
            return {}
    
    def _calculate_stability_score(self, detailed_results: Dict) -> float:
        """Calculate emotional stability score (0-1, higher = more stable)"""
        try:
            emotion_counts = detailed_results.get("emotion_counts", {})
            if not emotion_counts:
                return 0.5
            
            total = sum(emotion_counts.values())
            # Calculate entropy
            probabilities = [count / total for count in emotion_counts.values()]
            entropy = -sum(p * np.log(p + 1e-10) for p in probabilities)
            
            # Normalize (max entropy for 7 emotions = log(7))
            max_entropy = np.log(7)
            stability = 1 - (entropy / max_entropy)
            
            return round(stability, 3)
            
        except Exception:
            return 0.5
    
    def _analyze_stress_progression(self, frames: List[Dict]) -> Dict[str, Any]:
        """Analyze stress progression throughout session"""
        try:
            stress_timeline = []
            
            for frame in frames:
                result = self.analyze_frame(frame, apply_smoothing=False)
                if result.get("success"):
                    stress_timeline.append(result.get("stress_score", 0))
            
            if not stress_timeline:
                return {}
            
            # Calculate trend
            x = np.arange(len(stress_timeline))
            coeffs = np.polyfit(x, stress_timeline, 1)
            trend = "increasing" if coeffs[0] > 0.1 else "decreasing" if coeffs[0] < -0.1 else "stable"
            
            return {
                "initial_stress": stress_timeline[0],
                "final_stress": stress_timeline[-1],
                "peak_stress": max(stress_timeline),
                "min_stress": min(stress_timeline),
                "trend": trend,
                "trend_coefficient": round(coeffs[0], 3)
            }
            
        except Exception:
            return {}
    
    def _identify_peak_emotions(self, detailed_results: Dict) -> List[Dict]:
        """Identify peak emotions during session"""
        try:
            emotion_counts = detailed_results.get("emotion_counts", {})
            total = sum(emotion_counts.values())
            
            peaks = []
            for emotion, count in emotion_counts.items():
                percentage = (count / total * 100) if total > 0 else 0
                if percentage >= 20:  # Consider emotions that appear in >20% of frames
                    peaks.append({
                        "emotion": emotion,
                        "count": count,
                        "percentage": round(percentage, 1)
                    })
            
            return sorted(peaks, key=lambda x: x["percentage"], reverse=True)
            
        except Exception:
            return []
    
    def _assess_analysis_quality(self, result: Dict) -> str:
        """Assess overall analysis quality"""
        try:
            confidence = result.get("confidence", 0)
            quality = result.get("quality", "unknown")
            
            if confidence >= 0.8 and quality == "excellent":
                return "high"
            elif confidence >= 0.6:
                return "medium"
            else:
                return "low"
                
        except Exception:
            return "unknown"
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """Get information about the analyzer"""
        return {
            "model_loaded": self.model.loaded if self.model else False,
            "model_path": self.model.model_path if self.model else None,
            "emotion_labels": self.model.EMOTION_LABELS if self.model else [],
            "analysis_count": self._analysis_count,
            "configuration": {
                "use_confidence_weighting": self.use_confidence_weighting,
                "temporal_smoothing": self.temporal_smoothing,
                "outlier_rejection": self.outlier_rejection,
                "smoothing_window": self.smoothing_window
            }
        }
    
    def reset_smoothing(self):
        """Reset temporal smoothing buffer"""
        self._recent_emotions.clear()
        logger.info("🔄 Temporal smoothing reset")


# Create global analyzer instance
dominant_emotion_analyzer = DominantEmotionAnalyzer()