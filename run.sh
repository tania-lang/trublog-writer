#!/bin/bash

# SEO Blog Generator - Setup and Run Script
# ==========================================

echo "🚀 SEO Blog Generator Setup"
echo "=========================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API key"
fi

# Run the application
echo ""
echo "✅ Setup complete!"
echo "🌐 Starting application..."
echo ""
echo "The app will open in your browser at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app.py
