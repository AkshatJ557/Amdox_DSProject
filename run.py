#!/usr/bin/env python
"""
Enhanced Run Script for Amdox Backend Server
Includes dependency checking, MongoDB validation, and health monitoring
"""
import uvicorn
import sys
import os
from pathlib import Path
import time


# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(message: str, color: str = Colors.ENDC):
    """Print colored message"""
    print(f"{color}{message}{Colors.ENDC}")


def check_python_version():
    """Check if Python version is 3.9+"""
    print_colored("🐍 Checking Python version...", Colors.OKCYAN)
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_colored(f"❌ Python 3.9+ required. Current: {version.major}.{version.minor}", Colors.FAIL)
        print_colored("💡 Please upgrade Python: https://www.python.org/downloads/", Colors.WARNING)
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro}", Colors.OKGREEN)
    return True


def check_dependencies():
    """Check if required Python packages are installed"""
    print_colored("\n📦 Checking required packages...", Colors.OKCYAN)
    
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pymongo', 'PyMongo'),
        ('tensorflow', 'TensorFlow'),
        ('cv2', 'OpenCV'),
        ('streamlit', 'Streamlit')
    ]
    
    missing_packages = []
    
    for package_name, display_name in required_packages:
        try:
            __import__(package_name)
            print_colored(f"  ✅ {display_name}", Colors.OKGREEN)
        except ImportError:
            print_colored(f"  ❌ {display_name} - NOT INSTALLED", Colors.FAIL)
            missing_packages.append(package_name)
    
    if missing_packages:
        print_colored(f"\n❌ Missing packages: {', '.join(missing_packages)}", Colors.FAIL)
        print_colored("💡 Install with: pip install -r requirements.txt", Colors.WARNING)
        return False
    
    print_colored("✅ All required packages installed", Colors.OKGREEN)
    return True


def check_project_structure():
    """Check if required files and directories exist"""
    print_colored("\n📁 Checking project structure...", Colors.OKCYAN)
    
    current_dir = Path(__file__).parent
    
    required_items = {
        "backend/api.py": "API entry point",
        "backend/config.py": "Configuration file",
        "backend/controllers": "Controllers directory",
        "backend/services": "Services directory",
        "backend/database": "Database directory",
        "backend/ml/emotion": "ML models directory",
        "models": "Models directory",
        "frontend/components": "Frontend components",
        "frontend/pages": "Frontend pages"
    }
    
    all_exist = True
    
    for item, description in required_items.items():
        path = current_dir / item
        if path.exists():
            print_colored(f"  ✅ {description}", Colors.OKGREEN)
        else:
            print_colored(f"  ❌ {description} - NOT FOUND", Colors.WARNING)
            all_exist = False
    
    # Check for model file
    model_file = current_dir / "models" / "fer2013_mini_XCEPTION.102-0.66.hdf5"
    if model_file.exists():
        print_colored(f"  ✅ FER2013 emotion model", Colors.OKGREEN)
    else:
        print_colored(f"  ⚠️  FER2013 emotion model - NOT FOUND", Colors.WARNING)
        print_colored("     💡 Emotion detection will not work without the model", Colors.WARNING)
    
    return all_exist


def check_env_file():
    """Check if .env file exists and create template if missing"""
    print_colored("\n⚙️  Checking environment configuration...", Colors.OKCYAN)
    
    current_dir = Path(__file__).parent
    env_file = current_dir / ".env"
    
    if env_file.exists():
        print_colored("  ✅ .env file found", Colors.OKGREEN)
        return True
    else:
        print_colored("  ⚠️  .env file not found", Colors.WARNING)
        
        create = input("  💡 Create .env template? (y/n): ").lower().strip()
        
        if create == 'y':
            env_template = """# Amdox Environment Configuration

# MongoDB Configuration
MONGODB_URI=mongodb+srv://akshat:akshat@cluster0.3lfsels.mongodb.net/
DATABASE_NAME=amdox_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080

# Frontend Configuration
FRONTEND_PORT=8501

# Model Configuration
MODEL_PATH=models/fer2013_mini_XCEPTION.102-0.66.hdf5

# Logging
LOG_LEVEL=INFO

# Security (Optional)
# JWT_SECRET=your-secret-key-here
# JWT_ALGORITHM=HS256
"""
            env_file.write_text(env_template)
            print_colored("  ✅ Created .env template", Colors.OKGREEN)
            print_colored("  💡 Please update MongoDB credentials in .env", Colors.WARNING)
            return True
        else:
            print_colored("  ⚠️  Running with default configuration", Colors.WARNING)
            return False


def check_mongodb_connection():
    """Check if MongoDB connection is available"""
    print_colored("\n🗄️  Checking MongoDB connection...", Colors.OKCYAN)
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb+srv://akshat:akshat@cluster0.3lfsels.mongodb.net/')
        
        # Try to connect
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Ping the server
        client.admin.command('ping')
        
        # Get database info
        db_name = os.getenv('DATABASE_NAME', 'amdox_db')
        db = client[db_name]
        
        print_colored(f"  ✅ Connected to MongoDB", Colors.OKGREEN)
        print_colored(f"  📊 Database: {db_name}", Colors.OKBLUE)
        
        # Check collections
        collections = db.list_collection_names()
        if collections:
            print_colored(f"  📁 Collections: {', '.join(collections)}", Colors.OKBLUE)
        else:
            print_colored(f"  📁 No collections yet (will be created on first use)", Colors.OKBLUE)
        
        client.close()
        return True
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print_colored(f"  ❌ MongoDB connection failed", Colors.FAIL)
        print_colored(f"  💡 Error: {str(e)}", Colors.WARNING)
        print_colored(f"  💡 Check your MongoDB URI in .env file", Colors.WARNING)
        return False
    except Exception as e:
        print_colored(f"  ⚠️  Could not check MongoDB: {str(e)}", Colors.WARNING)
        return False


def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║             🎯  AMDOX BACKEND SERVER  🎯                 ║
    ║                                                           ║
    ║        AI-Powered Employee Wellness System                ║
    ║              Emotion Detection & Analysis                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print_colored(banner, Colors.HEADER)


def print_server_info():
    """Print server startup information"""
    print_colored("\n" + "="*60, Colors.OKBLUE)
    print_colored("🌐 Server Information", Colors.BOLD)
    print_colored("="*60, Colors.OKBLUE)
    print_colored("  📍 Backend API:  http://localhost:8080", Colors.OKCYAN)
    print_colored("  📚 API Docs:     http://localhost:8080/docs", Colors.OKCYAN)
    print_colored("  📖 ReDoc:        http://localhost:8080/redoc", Colors.OKCYAN)
    print_colored("  🏥 Health:       http://localhost:8080/health", Colors.OKCYAN)
    print_colored("="*60 + "\n", Colors.OKBLUE)


def check_port_available(port: int = 8080) -> bool:
    """Check if port is available"""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except OSError:
        return False


def main():
    """Main entry point"""
    
    # Print banner
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print_colored("\n❌ Please install missing dependencies first", Colors.FAIL)
        sys.exit(1)
    
    # Check project structure
    if not check_project_structure():
        print_colored("\n⚠️  Some project files are missing", Colors.WARNING)
        proceed = input("Continue anyway? (y/n): ").lower().strip()
        if proceed != 'y':
            sys.exit(1)
    
    # Check .env file
    check_env_file()
    
    # Check MongoDB connection
    if not check_mongodb_connection():
        print_colored("\n⚠️  MongoDB connection unavailable", Colors.WARNING)
        proceed = input("Continue anyway? (y/n): ").lower().strip()
        if proceed != 'y':
            sys.exit(1)
    
    # Check port availability
    print_colored("\n🔌 Checking port 8080...", Colors.OKCYAN)
    if not check_port_available(8080):
        print_colored("  ❌ Port 8080 is already in use", Colors.FAIL)
        print_colored("  💡 Stop the process using: lsof -i :8080", Colors.WARNING)
        print_colored("  💡 Or change port in backend/config.py", Colors.WARNING)
        sys.exit(1)
    print_colored("  ✅ Port 8080 is available", Colors.OKGREEN)
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Print server info
    print_server_info()
    
    print_colored("🚀 Starting FastAPI server...", Colors.OKGREEN)
    print_colored("   Press CTRL+C to stop\n", Colors.OKCYAN)
    
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
        print_colored("\n\n👋 Server stopped by user", Colors.WARNING)
        print_colored("="*60, Colors.OKBLUE)
    except Exception as e:
        print_colored(f"\n❌ Error starting server: {e}", Colors.FAIL)
        print_colored("\n💡 Troubleshooting tips:", Colors.WARNING)
        print_colored("1. Make sure you're in the Amdox_DSProject directory", Colors.OKCYAN)
        print_colored("2. Check if port 8080 is already in use: lsof -i :8080", Colors.OKCYAN)
        print_colored("3. Verify Python dependencies: pip install -r requirements.txt", Colors.OKCYAN)
        print_colored("4. Check MongoDB connection in .env file", Colors.OKCYAN)
        print_colored("5. Check backend/api.py for syntax errors", Colors.OKCYAN)
        sys.exit(1)


if __name__ == "__main__":
    main()