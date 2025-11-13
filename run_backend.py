"""Quick Start Script - Backend"""

import os
import sys
import subprocess

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ All requirements installed")
        return True
    except ImportError as e:
        print(f"❌ Missing requirements: {e}")
        print("\nPlease run: pip install -r requirements_production.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists(".env"):
        print("⚠️  .env file not found!")
        print("\nCreating .env from .env.example...")
        
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env file created")
            print("\n⚠️  IMPORTANT: Edit .env and add your API keys!")
            return False
        else:
            print("❌ .env.example not found!")
            return False
    
    print("✅ .env file exists")
    return True

def init_database():
    """Initialize database"""
    try:
        from database import init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def run_server():
    """Run the FastAPI server"""
    print("\n" + "="*60)
    print("🚀 Starting Backend Server...")
    print("="*60)
    print("\nAPI will be available at:")
    print("  • http://localhost:8000")
    print("  • Documentation: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "production_api:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")

def main():
    print("="*60)
    print("🚀 Dynamic LLM Router - Backend Startup")
    print("="*60 + "\n")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check .env
    if not check_env_file():
        print("\n⚠️  Please edit .env file and add your API keys, then run again.")
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        sys.exit(1)
    
    # Run server
    run_server()

if __name__ == "__main__":
    main()
