"""
Application Configuration
Loads settings from environment variables with sensible defaults
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Application settings
APP_NAME = os.getenv("APP_NAME", "Amdox Emotion Detection System")
VERSION = os.getenv("VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://akshat:akshat@cluster0.3lfsels.mongodb.net/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "amdox_db")

# Session configuration
SESSION_DURATION = int(os.getenv("SESSION_DURATION", 20))  # minutes
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 30))  # minutes

# Emotion Detection settings
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
STRESS_EMOTIONS = ['Sad', 'Angry', 'Fear', 'Disgust']
STRESS_THRESHOLD = int(os.getenv("STRESS_THRESHOLD", 3))
HIGH_STRESS_THRESHOLD = int(os.getenv("HIGH_STRESS_THRESHOLD", 7))

# Alert configuration
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", 15))
MAX_DAILY_ALERTS = int(os.getenv("MAX_DAILY_ALERTS", 5))

# Recommendation settings
RECOMMENDATION_CONFIDENCE_THRESHOLD = float(os.getenv("RECOMMENDATION_CONFIDENCE_THRESHOLD", 0.6))

# Model configuration
MODEL_PATH = os.getenv("MODEL_PATH", "models/fer2013_mini_XCEPTION.102-0.66.hdf5")
EMOTION_MODEL_PATH = os.path.join(Path(__file__).parent.parent, "models", "fer2013_mini_XCEPTION.102-0.66.hdf5")

# File paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "amdox.log"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Frontend configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

# Database session store (for future Redis implementation)
REDIS_URL = os.getenv("REDIS_URL", None)

# Recommendation weights (for ML-based recommendations)
EMOTION_WEIGHTS = {
    'Happy': {'creative': 0.9, 'analytical': 0.7, 'routine': 0.5},
    'Neutral': {'creative': 0.6, 'analytical': 0.8, 'routine': 0.9},
    'Sad': {'creative': 0.5, 'analytical': 0.6, 'routine': 0.7},
    'Angry': {'creative': 0.3, 'analytical': 0.4, 'routine': 0.5},
    'Fear': {'creative': 0.4, 'analytical': 0.5, 'routine': 0.6},
    'Disgust': {'creative': 0.5, 'analytical': 0.6, 'routine': 0.5},
    'Surprise': {'creative': 0.9, 'analytical': 0.7, 'routine': 0.4}
}

# Task recommendations by emotion
TASK_RECOMMENDATIONS = {
    'Happy': {
        'category': 'Creative',
        'tasks': [
            "Brainstorm new ideas for your project",
            "Start a creative side project",
            "Collaborate with team members on innovative solutions",
            "Document your creative process",
            "Share your positive energy with the team"
        ],
        'priority': 'Medium-High',
        'duration': '45-60 minutes'
    },
    'Neutral': {
        'category': 'General',
        'tasks': [
            "Review and organize your to-do list",
            "Catch up on emails and messages",
            "Prepare for upcoming meetings",
            "Update project documentation",
            "Review recent progress on goals"
        ],
        'priority': 'Medium',
        'duration': '30-45 minutes'
    },
    'Sad': {
        'category': 'Wellness',
        'tasks': [
            "Take a short walk outside",
            "Practice deep breathing exercises",
            "Listen to calming music",
            "Write down three things you're grateful for",
            "Reach out to a colleague for a brief chat"
        ],
        'priority': 'High',
        'duration': '15-20 minutes'
    },
    'Angry': {
        'category': 'Calming',
        'tasks': [
            "Practice the 4-7-8 breathing technique",
            "Take a brief meditation break",
            "Write down what's causing frustration",
            "Do a quick physical exercise (stretching or walking)",
            "Step away from the screen for 5 minutes"
        ],
        'priority': 'High',
        'duration': '10-15 minutes'
    },
    'Fear': {
        'category': 'Focus',
        'tasks': [
            "Break down complex tasks into smaller steps",
            "Review your progress on challenging projects",
            "Create a prioritized action plan",
            "Seek clarification on ambiguous requirements",
            "Practice positive self-talk"
        ],
        'priority': 'Medium-High',
        'duration': '30-45 minutes'
    },
    'Disgust': {
        'category': 'Productivity',
        'tasks': [
            "Clean and organize your workspace",
            "Declutter your digital files",
            "Review and improve existing processes",
            "Take a refreshing break",
            "Do a quick task that provides satisfaction"
        ],
        'priority': 'Medium',
        'duration': '20-30 minutes'
    },
    'Surprise': {
        'category': 'Exploration',
        'tasks': [
            "Learn something new related to your work",
            "Explore a new tool or technology",
            "Research emerging trends in your field",
            "Experiment with a new approach",
            "Share interesting findings with the team"
        ],
        'priority': 'Medium',
        'duration': '30-45 minutes'
    }
}

# Stress level thresholds
STRESS_LEVELS = {
    'Low': (0, 2),
    'Moderate': (3, 5),
    'High': (6, 7),
    'Very High': (8, 10)
}


def get_emotion_config(emotion: str) -> Dict:
    """Get configuration for a specific emotion"""
    return TASK_RECOMMENDATIONS.get(emotion, TASK_RECOMMENDATIONS['Neutral'])


def get_stress_level(score: int) -> str:
    """Get stress level label from score"""
    for level, (low, high) in STRESS_LEVELS.items():
        if low <= score <= high:
            return level
    return 'Very High' if score > 7 else 'Low'


def load_custom_config(config_file: Optional[str] = None) -> Dict:
    """
    Load custom configuration from file
    
    Args:
        config_file: Path to custom config file (JSON or YAML)
    
    Returns:
        dict: Custom configuration
    """
    if config_file is None:
        config_file = os.getenv("CUSTOM_CONFIG_FILE", None)
    
    if config_file is None or not os.path.exists(config_file):
        return {}
    
    # Import based on file type
    if config_file.endswith('.json'):
        import json
        with open(config_file, 'r') as f:
            return json.load(f)
    elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
        import yaml
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    return {}


def validate_config() -> tuple:
    """
    Validate required configuration settings
    
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # Check MongoDB connection
    if not MONGO_URI:
        errors.append("MONGO_URI is not set")
    
    # Check session duration
    if SESSION_DURATION < 1:
        errors.append("SESSION_DURATION must be at least 1 minute")
    
    # Check stress threshold
    if not 0 <= STRESS_THRESHOLD <= 10:
        errors.append("STRESS_THRESHOLD must be between 0 and 10")
    
    # Check model path
    if not os.path.exists(EMOTION_MODEL_PATH):
        print(f"⚠️ Warning: Emotion model not found at {EMOTION_MODEL_PATH}")
    
    return (len(errors) == 0, errors)


# Print configuration summary on import
if __name__ == "__main__":
    print("📋 Amdox Configuration Summary")
    print("="*50)
    print(f"App: {APP_NAME} v{VERSION}")
    print(f"Debug: {DEBUG}")
    print(f"Server: {HOST}:{PORT}")
    print(f"Database: {MONGO_DB_NAME}")
    print(f"Session Duration: {SESSION_DURATION} minutes")
    print(f"Stress Threshold: {STRESS_THRESHOLD}")
    print(f"Model Path: {EMOTION_MODEL_PATH}")
    print("="*50)
    
    # Validate configuration
    is_valid, errors = validate_config()
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")

