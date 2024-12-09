#!/bin/bash

sleep 1

echo "╔════════════════════════════════════════╗"
echo "║         VitalWatch Installation        ║"
echo "╚════════════════════════════════════════╝"

sleep 2

# Set variables for installation paths
INSTALL_DIR="$HOME/.vitalwatch"
ENV_DIR="$INSTALL_DIR/env"
APPLICATION_PATH="$INSTALL_DIR/run.py"
DESKTOP_ENTRY="$INSTALL_DIR/VitalWatch.desktop"
LOCAL_APPLICATIONS="$HOME/.local/share/applications"

# Step 1: Create installation directory
echo "[1/7] Creating installation directory..."
mkdir -p "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create installation directory."
    exit 1
fi

# Step 2: Set up Python virtual environment
echo "[2/7] Setting up Python virtual environment..."
# Ensure python3 is used
PYTHON=$(which python3 || which python)
if [ -z "$PYTHON" ]; then
    echo "Error: Python is not installed or not found in PATH."
    exit 1
fi
$PYTHON -m venv "$ENV_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create Python virtual environment."
    exit 1
fi
source "$ENV_DIR/bin/activate"

# Step 3: Install required dependencies
echo "[3/7] Installing required dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

# Step 4: Copy application files
echo "[4/7] Copying application files..."
cp -r ./* "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Failed to copy application files."
    exit 1
fi

# Step 5: Create desktop entry
echo "[5/7] Creating desktop entry..."
mkdir -p "$LOCAL_APPLICATIONS"
cp "$DESKTOP_ENTRY" "$LOCAL_APPLICATIONS/"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create desktop entry."
    exit 1
fi

# Step 6: Set file permissions
echo "[6/7] Setting file permissions..."
chmod +x "$APPLICATION_PATH"
chmod -R 755 "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set file permissions."
    exit 1
fi

# Final Message and Starting Application
echo "✓ Installation completed successfully!"
echo "╔════════════════════════════════════════╗"
echo "║       VitalWatch is monitoring you!    ║"
echo "╚════════════════════════════════════════╝"

# Instructions for running the app
echo "VitalWatch has been successfully installed."
echo "You can now use the application from the application menu, which was added during installation."
echo "Just search for 'VitalWatch' in your application menu and click to launch it."
echo ""
# Fallback instructions if application menu fails
echo "If for some reason the application menu doesn't work, you can use the following steps to run VitalWatch manually:"
echo "1. Open a terminal window."
echo "2. Activate the virtual environment by running:"
echo "   source $ENV_DIR/bin/activate"
echo "3. Run the application by executing:"
echo "   python $APPLICATION_PATH"