"""
Emotion detection ML module
"""

from backend.ml.emotion.emotion_model import emotion_model
from backend.ml.emotion.dominant_emotion import dominant_emotion_analyzer

__all__ = [
    "emotion_model",
    "dominant_emotion_analyzer"
]

