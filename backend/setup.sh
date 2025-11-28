#!/bin/bash

# CyberShield Backend Setup Script

echo "🚀 Setting up CyberShield Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - GROQ_API_KEY: Get from https://console.groq.com"
    echo "   - HF_TOKEN: Get from https://huggingface.co/settings/tokens"
    echo "   - SECRET_KEY: Generate with: openssl rand -hex 32"
else
    echo "✅ .env file already exists"
fi

# Create evidence directories
echo "📁 Creating evidence directories..."
mkdir -p evidence/screenshots
mkdir -p evidence/logs

echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python main.py"
echo "  3. Or: uvicorn main:app --reload"

