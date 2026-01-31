#!/usr/bin/env python
"""
Run script for Amdox Backend Server hehe
"""
import uvicorn
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required files exist"""
    current_dir = Path(__file__).parent
    
    # Check for backend/api.py
    api_file = current_dir / "backend" / "api.py"
    if not api_file.exists():
        print(f"❌ Error: {api_file} not found!")
        print("💡 Make sure you're in the project root directory")
        return False
    
    # Check for config.py
    config_file = current_dir / "backend" / "config.py"
    if not config_file.exists():
        print(f"⚠️ Warning: {config_file} not found")
        print("💡 Running with default configuration")
    
    # Check for .env file
    env_file = current_dir / ".env"
    if not env_file.exists():
        print(f"⚠️ Warning: {env_file} not found")
        print("💡 Using default environment variables")
    
    # Check for model file
    model_file = current_dir / "models" / "fer2013_mini_XCEPTION.102-0.66.hdf5"
    if not model_file.exists():
        print(f"⚠️ Warning: Model file not found at {model_file}")
        print("💡 Emotion detection will not work without the model")
    
    return True

def main():
    print("🚀 Launching Amdox Emotion Detection Backend Server...")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print("📁 Project root:", current_dir)
    print("🔧 Starting FastAPI server...")
    print("="*60)
    
    try:
        # Run the server
        uvicorn.run(
            "backend.api:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info",
            access_log=True,
            use_colors=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you're in the Amdox_DSProject directory")
        print("2. Check if port 8080 is already in use: lsof -i :8080")
        print("3. Verify Python dependencies: pip install -r requirements.txt")
        print("4. Check MongoDB connection in .env file")
        sys.exit(1)

if __name__ == "__main__":
    main()

