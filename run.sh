#!/bin/bash

# VENTYY Recommendation Microservice - Run Script

echo "🚀 Starting VENTYY Recommendation Microservice..."

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the service
echo "Starting service on http://localhost:8000"
echo "Swagger UI available at http://localhost:8000/docs"
echo ""

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
