#!/bin/bash
# Setup script for AI Calling System

set -e

echo "🚀 Setting up AI Calling System..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-updated.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs static/css static/js templates

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values"
fi

# Initialize database
echo "🗄️ Initializing database..."
python -c "
from src.core.database import DatabaseService
from src.config.settings import settings
db = DatabaseService(settings.database.path)
print('Database initialized successfully')
"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Synthflow API key and configuration"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python -m src.web.app"
echo "4. Open: http://localhost:5000"