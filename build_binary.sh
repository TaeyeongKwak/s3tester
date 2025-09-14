#!/bin/bash

# S3Tester Binary Build Script

set -e

echo "🔧 S3Tester Binary Build Script"
echo "================================"

# Check if virtual environment is active
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "❌ Virtual environment not detected. Please activate your virtual environment first:"
    echo "   source venv/bin/activate  # Linux/macOS"
    echo "   venv\\Scripts\\activate     # Windows"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install -e ".[build]"

# Clean previous builds
echo "🧹 Cleaning previous build artifacts..."
rm -rf build/ dist/ __pycache__/
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Run PyInstaller
echo "🔨 Building binary executable..."
pyinstaller s3tester.spec

# Check if build was successful
if [[ -f "dist/s3tester" ]] || [[ -f "dist/s3tester.exe" ]]; then
    echo "✅ Binary executable built successfully!"
    echo "📍 Location: dist/"
    ls -la dist/
    
    echo ""
    echo "🚀 Test the executable:"
    if [[ -f "dist/s3tester" ]]; then
        echo "   ./dist/s3tester --version"
        echo "   ./dist/s3tester --help"
    else
        echo "   dist\\s3tester.exe --version"
        echo "   dist\\s3tester.exe --help"
    fi
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi

echo ""
echo "✨ Build completed successfully!"