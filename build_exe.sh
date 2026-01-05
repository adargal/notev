#!/bin/bash
# Notev Build Script for Linux/Mac
# Creates a standalone executable using PyInstaller

echo "============================================================"
echo "  Notev Build Script"
echo "============================================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Check if PyInstaller is installed
if ! pip show pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Install dependencies
echo
echo "Installing dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo
echo "Cleaning previous builds..."
rm -rf build dist

# Build the executable
echo
echo "Building Notev executable..."
pyinstaller notev.spec --clean

# Check if build succeeded
if [ -f "dist/Notev/Notev" ]; then
    echo
    echo "============================================================"
    echo "  BUILD SUCCESSFUL!"
    echo "============================================================"
    echo
    echo "Your distributable is in: dist/Notev/"
    echo
    echo "To run: ./dist/Notev/Notev"
    echo
    echo "To distribute, copy the entire 'dist/Notev' folder."
else
    echo
    echo "============================================================"
    echo "  BUILD FAILED"
    echo "============================================================"
    echo "Please check the error messages above."
    exit 1
fi
