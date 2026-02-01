#!/usr/bin/env python3
"""
Seed database with test data for Amdox
"""
import requests
import random
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080"

def create_users():
    """Create test users"""
    users = [
        {"user_id": "EMP001", "name": "John Doe", "email": "john@company.com", "role": "employee", "team_id": "TEAM001"},
        {"user_id": "EMP002", "name": "Jane Smith", "email": "jane@company.com", "role": "employee", "team_id": "TEAM001"},
        {"user_id": "EMP003", "name": "Bob Wilson", "email": "bob@company.com", "role": "employee", "team_id": "TEAM002"},
        {"user_id": "MGR001", "name": "Alice Manager", "email": "alice@company.com", "role": "manager", "team_id": "TEAM001"},
        {"user_id": "HR001", "name": "HR Admin", "email": "hr@company.com", "role": "hr"},
    ]
    
    print("👥 Creating users...")
    for user in users:
        try:
            response = requests.post(f"{API_BASE}/users/create", json=user, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Created user: {user['user_id']}")
            else:
                print(f"  ⚠️ User {user['user_id']} might already exist")
        except Exception as e:
            print(f"  ❌ Error creating {user['user_id']}: {e}")


def create_teams():
    """Create test teams"""
    teams = [
        {"team_id": "TEAM001", "name": "Development Team", "manager_id": "MGR001", "members": ["EMP001", "EMP002"]},
        {"team_id": "TEAM002", "name": "Marketing Team", "manager_id": "MGR001", "members": ["EMP003"]},
    ]
    
    print("\n🏢 Creating teams...")
    for team in teams:
        try:
            response = requests.post(f"{API_BASE}/teams/create", json=team, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Created team: {team['team_id']}")
            else:
                print(f"  ⚠️ Team {team['team_id']} might already exist")
        except Exception as e:
            print(f"  ❌ Error creating {team['team_id']}: {e}")


def create_mood_entries():
    """Create test mood entries"""
    print("\n😊 Creating mood entries...")
    
    emotions = ["Happy", "Sad", "Neutral", "Angry", "Surprise", "Fear", "Disgust"]
    users = ["EMP001", "EMP002", "EMP003"]
    
    # Create entries for the last 7 days
    for user_id in users:
        for day in range(7):
            for _ in range(random.randint(2, 5)):  # 2-5 entries per day
                emotion = random.choice(emotions)
                stress = random.randint(1, 10)
                
                # Create probability distribution
                probs = {e: random.random() * 0.2 for e in emotions}
                probs[emotion] = 0.6 + random.random() * 0.3  # Dominant emotion
                
                # Normalize
                total = sum(probs.values())
                probs = {k: v/total for k, v in probs.items()}
                
                entry = {
                    "user_id": user_id,
                    "dominant_emotion": emotion,
                    "emotion_probabilities": probs,
                    "stress_score": stress,
                    "confidence": 0.7 + random.random() * 0.25,
                    "timestamp": (datetime.now() - timedelta(days=day, hours=random.randint(0, 23))).isoformat()
                }
                
                try:
                    response = requests.post(f"{API_BASE}/mood/create", json=entry, timeout=5)
                    if response.status_code == 200:
                        print(f"  ✅ Created mood entry for {user_id} ({emotion}, stress: {stress})")
                except Exception as e:
                    print(f"  ❌ Error: {e}")


def main():
    print("🌱 Seeding Amdox database with test data...")
    print("=" * 60)
    
    try:
        # Check if API is running (accept 503 for now)
        response = requests.get(f"{API_BASE}/health", timeout=5)
        
        # Accept both 200 and 503 as "server is running"
        if response.status_code not in [200, 503]:
            print(f"❌ API returned unexpected status: {response.status_code}")
            return
        
        print("✅ API is running (status:", response.status_code, ")")
        
        # Try to get actual health status
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("⚠️ Health check degraded, but continuing...")
        
        print("=" * 60)
        
        # Create data
        create_users()
        create_teams()
        create_mood_entries()
        
        
        print("\n" + "=" * 60)
        print("✅ Database seeding completed!")
        print("\n📊 You can now:")
        print("  - Login with user_id: EMP001")
        print("  - View dashboard with real data")
        print("  - Test all features")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at http://localhost:8080")
        print("💡 Make sure the backend server is running: python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()