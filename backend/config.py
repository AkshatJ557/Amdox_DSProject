"""
Enhanced Configuration for Amdox - ALIGNED WITH NOTEBOOK
Task zones from notebook: Green/Yellow/Orange/Red
"""

# ============================================================================
# EMOTION LABELS (FER2013 Model)
# ============================================================================
EMOTION_LABELS = [
    'Angry',
    'Disgust',
    'Fear',
    'Happy',
    'Sad',
    'Surprise',
    'Neutral'
]

# ============================================================================
# TASK ZONES - ALIGNED WITH NOTEBOOK (Cell 5-6)
# ============================================================================
# Green Zone: Creative, High Energy
# Yellow Zone: Routine, Moderate Energy
# Orange Zone: Low Energy, Supportive
# Red Zone: Recovery, Rest

TASK_ZONES = {
    'GREEN': {
        'name': 'Green_Creative_Task',
        'description': 'High energy, creative, collaborative tasks',
        'energy_level': 'high',
        'stress_range': (0, 3),
        'color': '#4CAF50'
    },
    'YELLOW': {
        'name': 'Yellow_Routine_Task',
        'description': 'Routine, structured, moderate energy tasks',
        'energy_level': 'moderate',
        'stress_range': (3, 5),
        'color': '#FFC107'
    },
    'ORANGE': {
        'name': 'Orange_LowEnergy_Task',
        'description': 'Light, supportive, low energy tasks',
        'energy_level': 'low',
        'stress_range': (5, 7),
        'color': '#FF9800'
    },
    'RED': {
        'name': 'Red_Recovery_Task',
        'description': 'Recovery, rest, stress relief activities',
        'energy_level': 'minimal',
        'stress_range': (7, 10),
        'color': '#F44336'
    }
}

# ============================================================================
# EMOTION → TASK ZONE MAPPING
# ============================================================================
EMOTION_TO_ZONE = {
    'Happy': 'GREEN',
    'Surprise': 'YELLOW',
    'Neutral': 'YELLOW',
    'Sad': 'ORANGE',
    'Fear': 'ORANGE',
    'Disgust': 'RED',
    'Angry': 'RED'
}

# ============================================================================
# COMPREHENSIVE TASK RECOMMENDATIONS
# ============================================================================
TASK_RECOMMENDATIONS = {
    # ========== GREEN ZONE: HAPPY ==========
    'Happy': {
        'zone': 'GREEN',
        'zone_name': 'Green_Creative_Task',
        'tasks': [
            {
                'task': 'Brainstorm innovative solutions for current project',
                'category': 'Creative',
                'priority': 'High',
                'duration': '30-60 minutes',
                'energy_required': 'High',
                'description': 'Channel positive energy into creative problem-solving'
            },
            {
                'task': 'Lead a creative brainstorming session with team',
                'category': 'Teamwork',
                'priority': 'High',
                'duration': '45-90 minutes',
                'energy_required': 'High',
                'description': 'Your enthusiasm will energize the team'
            },
            {
                'task': 'Work on strategic planning or innovation projects',
                'category': 'Innovation',
                'priority': 'High',
                'duration': '60-120 minutes',
                'energy_required': 'High',
                'description': 'Perfect state for big-picture thinking'
            },
            {
                'task': 'Mentor a colleague or conduct training session',
                'category': 'Teamwork',
                'priority': 'Medium',
                'duration': '30-60 minutes',
                'energy_required': 'High',
                'description': 'Share your positive energy with others'
            },
            {
                'task': 'Tackle challenging problem that requires creativity',
                'category': 'Creative',
                'priority': 'High',
                'duration': '45-90 minutes',
                'energy_required': 'High',
                'description': 'Use peak mental state for complex challenges'
            }
        ]
    },
    
    # ========== YELLOW ZONE: SURPRISE ==========
    'Surprise': {
        'zone': 'YELLOW',
        'zone_name': 'Yellow_Routine_Task',
        'tasks': [
            {
                'task': 'Explore new tools or technologies',
                'category': 'Learning',
                'priority': 'Medium',
                'duration': '30-60 minutes',
                'energy_required': 'Moderate',
                'description': 'Channel curiosity into learning'
            },
            {
                'task': 'Research industry trends and innovations',
                'category': 'Learning',
                'priority': 'Medium',
                'duration': '45-90 minutes',
                'energy_required': 'Moderate',
                'description': 'Great time for discovery and exploration'
            },
            {
                'task': 'Attend webinar or training on new topic',
                'category': 'Learning',
                'priority': 'Medium',
                'duration': '60-120 minutes',
                'energy_required': 'Moderate',
                'description': 'Embrace the learning opportunity'
            },
            {
                'task': 'Experiment with different approach to current task',
                'category': 'Innovation',
                'priority': 'Medium',
                'duration': '30-60 minutes',
                'energy_required': 'Moderate',
                'description': 'Try something new while energy is present'
            },
            {
                'task': 'Document recent learnings or discoveries',
                'category': 'Documentation',
                'priority': 'Low',
                'duration': '20-40 minutes',
                'energy_required': 'Moderate',
                'description': 'Capture insights while they\'re fresh'
            }
        ]
    },
    
    # ========== YELLOW ZONE: NEUTRAL ==========
    'Neutral': {
        'zone': 'YELLOW',
        'zone_name': 'Yellow_Routine_Task',
        'tasks': [
            {
                'task': 'Process and respond to emails',
                'category': 'Routine work',
                'priority': 'Medium',
                'duration': '30-45 minutes',
                'energy_required': 'Moderate',
                'description': 'Good focus for administrative tasks'
            },
            {
                'task': 'Update project documentation',
                'category': 'Documentation',
                'priority': 'Medium',
                'duration': '45-60 minutes',
                'energy_required': 'Moderate',
                'description': 'Steady state ideal for documentation'
            },
            {
                'task': 'Review and organize task lists',
                'category': 'Routine work',
                'priority': 'Medium',
                'duration': '20-30 minutes',
                'energy_required': 'Moderate',
                'description': 'Structure your work while focused'
            },
            {
                'task': 'Attend scheduled meetings or standups',
                'category': 'Teamwork',
                'priority': 'High',
                'duration': '30-60 minutes',
                'energy_required': 'Moderate',
                'description': 'Balanced state for participation'
            },
            {
                'task': 'Complete routine coding or development tasks',
                'category': 'Routine work',
                'priority': 'Medium',
                'duration': '60-120 minutes',
                'energy_required': 'Moderate',
                'description': 'Good concentration for standard tasks'
            }
        ]
    },
    
    # ========== ORANGE ZONE: SAD ==========
    'Sad': {
        'zone': 'ORANGE',
        'zone_name': 'Orange_LowEnergy_Task',
        'tasks': [
            {
                'task': 'Take a 15-minute walk outside',
                'category': 'Peer support',
                'priority': 'Critical',
                'duration': '15-20 minutes',
                'energy_required': 'Low',
                'description': 'Fresh air and movement can help'
            },
            {
                'task': 'Reach out to a trusted colleague for support',
                'category': 'Peer support',
                'priority': 'High',
                'duration': '15-30 minutes',
                'energy_required': 'Low',
                'description': 'Connection can improve mood'
            },
            {
                'task': 'Work on light, non-critical administrative tasks',
                'category': 'Light tasks',
                'priority': 'Low',
                'duration': '20-40 minutes',
                'energy_required': 'Low',
                'description': 'Easy tasks that don\'t require high focus'
            },
            {
                'task': 'Listen to uplifting music while organizing workspace',
                'category': 'Light tasks',
                'priority': 'Low',
                'duration': '15-30 minutes',
                'energy_required': 'Low',
                'description': 'Simple activity with mood-boosting potential'
            },
            {
                'task': 'Practice gratitude journaling',
                'category': 'Peer support',
                'priority': 'Medium',
                'duration': '10-15 minutes',
                'energy_required': 'Low',
                'description': 'Shift focus to positive aspects'
            }
        ]
    },
    
    # ========== ORANGE ZONE: FEAR ==========
    'Fear': {
        'zone': 'ORANGE',
        'zone_name': 'Orange_LowEnergy_Task',
        'tasks': [
            {
                'task': 'Break down intimidating task into smaller steps',
                'category': 'Guided work',
                'priority': 'High',
                'duration': '20-30 minutes',
                'energy_required': 'Low',
                'description': 'Reduce overwhelm through structure'
            },
            {
                'task': 'Pair program or work alongside colleague',
                'category': 'Guided work',
                'priority': 'High',
                'duration': '45-90 minutes',
                'energy_required': 'Low',
                'description': 'Support can reduce anxiety'
            },
            {
                'task': 'Review completed work for confidence boost',
                'category': 'Light tasks',
                'priority': 'Medium',
                'duration': '15-20 minutes',
                'energy_required': 'Low',
                'description': 'Remind yourself of capabilities'
            },
            {
                'task': 'Follow a detailed tutorial or guide',
                'category': 'Guided work',
                'priority': 'Medium',
                'duration': '30-45 minutes',
                'energy_required': 'Low',
                'description': 'Structure reduces uncertainty'
            },
            {
                'task': 'Create action plan with clear next steps',
                'category': 'Guided work',
                'priority': 'High',
                'duration': '20-30 minutes',
                'energy_required': 'Low',
                'description': 'Clarity reduces fear'
            }
        ]
    },
    
    # ========== RED ZONE: DISGUST ==========
    'Disgust': {
        'zone': 'RED',
        'zone_name': 'Red_Recovery_Task',
        'tasks': [
            {
                'task': 'Clean and organize workspace',
                'category': 'Physical activity',
                'priority': 'Medium',
                'duration': '15-30 minutes',
                'energy_required': 'Minimal',
                'description': 'Physical activity helps release tension'
            },
            {
                'task': 'Declutter digital files and folders',
                'category': 'Physical activity',
                'priority': 'Low',
                'duration': '20-40 minutes',
                'energy_required': 'Minimal',
                'description': 'Create order from chaos'
            },
            {
                'task': 'Take a break and practice deep breathing',
                'category': 'Break',
                'priority': 'Critical',
                'duration': '10-15 minutes',
                'energy_required': 'Minimal',
                'description': 'Reset emotional state'
            },
            {
                'task': 'Review and improve existing processes',
                'category': 'Physical activity',
                'priority': 'Medium',
                'duration': '30-45 minutes',
                'energy_required': 'Minimal',
                'description': 'Channel frustration into improvement'
            },
            {
                'task': 'Step away and change environment briefly',
                'category': 'Break',
                'priority': 'High',
                'duration': '10-20 minutes',
                'energy_required': 'Minimal',
                'description': 'Distance yourself from source'
            }
        ]
    },
    
    # ========== RED ZONE: ANGRY ==========
    'Angry': {
        'zone': 'RED',
        'zone_name': 'Red_Recovery_Task',
        'tasks': [
            {
                'task': 'Take immediate break - step away from work',
                'category': 'Break',
                'priority': 'Critical',
                'duration': '15-30 minutes',
                'energy_required': 'Minimal',
                'description': 'Prevent escalation'
            },
            {
                'task': 'Practice 4-7-8 breathing technique',
                'category': 'Stress recovery',
                'priority': 'Critical',
                'duration': '5-10 minutes',
                'energy_required': 'Minimal',
                'description': 'Calm nervous system immediately'
            },
            {
                'task': 'Go for a brisk walk or do physical exercise',
                'category': 'Physical activity',
                'priority': 'High',
                'duration': '15-30 minutes',
                'energy_required': 'Minimal',
                'description': 'Release physical tension'
            },
            {
                'task': 'Journal about frustrations (privately)',
                'category': 'Stress recovery',
                'priority': 'High',
                'duration': '10-20 minutes',
                'energy_required': 'Minimal',
                'description': 'Process emotions safely'
            },
            {
                'task': 'Listen to calming music or meditation audio',
                'category': 'Stress recovery',
                'priority': 'High',
                'duration': '10-20 minutes',
                'energy_required': 'Minimal',
                'description': 'Soothe emotional state'
            }
        ]
    }
}

# ============================================================================
# STRESS LEVEL CONFIGURATIONS
# ============================================================================
STRESS_LEVELS = {
    'very_low': {
        'range': (0, 2),
        'label': 'Very Low',
        'color': '#4CAF50',
        'icon': '😊',
        'action': 'Continue current activities'
    },
    'moderate': {
        'range': (3, 5),
        'label': 'Moderate',
        'color': '#FFC107',
        'icon': '😐',
        'action': 'Monitor and manage workload'
    },
    'high': {
        'range': (6, 7),
        'label': 'High',
        'color': '#FF9800',
        'icon': '😰',
        'action': 'Take breaks and reduce stress'
    },
    'very_high': {
        'range': (8, 10),
        'label': 'Very High',
        'color': '#F44336',
        'icon': '😫',
        'action': 'Immediate intervention required'
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_stress_level(score: int) -> str:
    """Get stress level label from score"""
    if score <= 2:
        return "Very Low"
    elif score <= 5:
        return "Moderate"
    elif score <= 7:
        return "High"
    else:
        return "Very High"

def get_task_zone_for_emotion(emotion: str) -> str:
    """Get task zone for an emotion"""
    return EMOTION_TO_ZONE.get(emotion, 'YELLOW')

def get_tasks_for_emotion(emotion: str) -> dict:
    """Get all tasks for a specific emotion"""
    return TASK_RECOMMENDATIONS.get(emotion, TASK_RECOMMENDATIONS['Neutral'])

def get_zone_info(zone: str) -> dict:
    """Get information about a task zone"""
    return TASK_ZONES.get(zone.upper(), TASK_ZONES['YELLOW'])

# ============================================================================
# EMOTION WEIGHTS FOR ML MODEL
# ============================================================================
EMOTION_WEIGHTS = {
    'Angry': 1.0,
    'Disgust': 0.9,
    'Fear': 0.8,
    'Happy': 0.3,
    'Sad': 0.7,
    'Surprise': 0.5,
    'Neutral': 0.4
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
MONGODB_URI = "mongodb+srv://akshat:akshat@cluster0.3lfsels.mongodb.net/"
DATABASE_NAME = "amdox_db"

# Collections
COLLECTIONS = {
    'users': 'users',
    'mood_entries': 'mood_entries',
    'teams': 'teams',
    'alerts': 'alerts',
    'recommendation_feedback': 'recommendation_feedback'
}

# ============================================================================
# SESSION CONFIGURATION
# ============================================================================
SESSION_DURATION_MINUTES = 20
SESSION_TIMEOUT_MINUTES = 30

# ============================================================================
# ALERT CONFIGURATION
# ============================================================================
STRESS_THRESHOLD_MODERATE = 3
STRESS_THRESHOLD_HIGH = 7
STRESS_THRESHOLD_CRITICAL = 9

ALERT_COOLDOWN_MINUTES = 15
ALERT_DAILY_LIMIT = 5

# ============================================================================
# API CONFIGURATION
# ============================================================================
API_HOST = "0.0.0.0"
API_PORT = 8080
API_RELOAD = True

# CORS
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8501",
    "http://localhost:3000",
]