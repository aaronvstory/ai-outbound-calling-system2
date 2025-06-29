"""
WSGI entry point for production deployment
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the Flask app
from src.web.app import create_app

# Create the application
app = create_app()

if __name__ == "__main__":
    app.run()