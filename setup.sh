#!/bin/bash
# IQOS Social Intelligence - Mac/Linux Setup Script
# Run this after cloning the repository

set -e  # Exit on error

echo "===================================="
echo "IQOS Social Intelligence Setup"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
python3 -m venv venv

echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo "[3/4] Installing dependencies..."
pip install -r requirements.txt

echo "[4/4] Verifying setup..."
if python3 run_analysis.py; then
    echo ""
    echo "===================================="
    echo "✅ Setup Complete!"
    echo "===================================="
    echo ""
    echo "To activate the environment in the future:"
    echo "  source venv/bin/activate"
    echo ""
    echo "To run the analysis:"
    echo "  python3 run_analysis.py"
    echo ""
else
    echo ""
    echo "⚠️  WARNING: Test run failed!"
    echo "Make sure you've copied the data files to:"
    echo "  - data/input/dataset_instagram-scraper_*.json"
    echo "  - data/images/*.jpg"
    echo ""
fi