#!/bin/bash

# Define the Python version you want to use (you can adjust this if necessary)
PYTHON_VERSION=python3

# Define the directory for the virtual environment
VENV_DIR="routersploit_env"

# Step 1: Update system packages
echo "[INFO] Updating system packages..."
sudo pacman -Syu --noconfirm

# Step 2: Install required packages (Python 3 and pip)
echo "[INFO] Installing Python 3 and pip..."
sudo pacman -S python python-pip --noconfirm

# Step 3: Create a virtual environment
echo "[INFO] Creating virtual environment..."
$PYTHON_VERSION -m venv $VENV_DIR

# Step 4: Activate the virtual environment
echo "[INFO] Activating virtual environment..."
source $VENV_DIR/bin/activate

# Step 5: Install required Python packages
echo "[INFO] Installing required Python packages..."
pip install --upgrade pip  # Upgrade pip to the latest version
pip install aiofiles asyncio

# Step 6: Inform the user to activate the virtual environment
echo "[INFO] Virtual environment setup is complete!"
echo "[INFO] To activate the virtual environment, run: source $VENV_DIR/bin/activate"
echo "[INFO] To deactivate the virtual environment, run: deactivate"
