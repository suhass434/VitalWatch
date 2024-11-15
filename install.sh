#!/bin/bash

sleep 1

echo "╔════════════════════════════════════════╗"
echo "║         VitalWatch Installation        ║"
echo "╚════════════════════════════════════════╝"

sleep 2

# Step 1: Creating installation directory
echo "[1/7] Creating installation directory..."
mkdir -p ~/.vitalwatch
if [ $? -ne 0 ]; then
    echo "Error: Failed to create installation directory."
    exit 1
fi

# Step 2: Setting up Python virtual environment
echo "[2/7] Setting up Python virtual environment..."
python -m venv ~/.vitalwatch/env
if [ $? -ne 0 ]; then
    echo "Error: Failed to create Python virtual environment."
    exit 1
fi
source ~/.vitalwatch/env/bin/activate

# Step 3: Installing required dependencies
echo "[3/7] Installing required dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

# Step 4: Copying application files
echo "[4/7] Copying application files..."
cp -r ./* ~/.vitalwatch
if [ $? -ne 0 ]; then
    echo "Error: Failed to copy application files."
    exit 1
fi

# Step 5: Creating desktop entry
echo "[5/7] Creating desktop entry..."
mkdir -p ~/.local/share/applications
cp VitalWatch.desktop ~/.local/share/applications/
if [ $? -ne 0 ]; then
    echo "Error: Failed to create desktop entry."
    exit 1
fi

# Step 6: Setting file permissions
echo "[6/7] Setting file permissions..."
chmod +x ~/.vitalwatch/run.py
chmod -R 755 ~/.vitalwatch
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
echo "   source ~/.vitalwatch/env/bin/activate"
echo "3. Run the application by executing:"
echo "   python ~/.vitalwatch/run.py"