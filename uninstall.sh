#!/bin/bash

echo "╔════════════════════════════════════════╗"
echo "║        Uninstalling VitalWatch         ║"
echo "╚════════════════════════════════════════╝"

# Step 1: Define paths
INSTALL_DIR="$HOME/.vitalwatch"              
VENV_DIR="$INSTALL_DIR/env"                 
DESKTOP_ENTRY="$HOME/.local/share/applications/VitalWatch.desktop"
CONFIG_FILE="$INSTALL_DIR/config/config.yaml"

echo  $INSTALL_DIR

sleep 1

# Step 2: Confirm uninstallation
read -p "Are you sure you want to uninstall VitalWatch? (y/n): " confirmation
if [[ "$confirmation" != "y" ]]; then
    echo "No worries! Your VitalWatch setup is safe. See you next time!"
    exit 0
fi

echo "Let's clear the stage! Time to uninstall VitalWatch."

# Step 3: Stop any running instances
echo "[1/6] Stopping any running instances..."
if pkill -f "$INSTALL_DIR/run.py" > /dev/null 2>&1; then
    echo "VitalWatch processes stopped successfully."
else
    echo "No running instances of VitalWatch found."
fi
echo "VitalWatch is now idle and ready to say goodbye."

# Step 4: Remove application files
echo "[2/6] Removing application files..."
if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    echo "Application files swept away from $INSTALL_DIR!"
else
    echo "Looks like the installation directory is already gone."
fi
echo "VitalWatch files have left your system."

# Step 5: Remove desktop entry
echo "[3/6] Removing desktop entry..."
if [[ -f "$DESKTOP_ENTRY" ]]; then
    rm "$DESKTOP_ENTRY"
    echo "Desktop shortcut removed. Out of sight, out of mind!"
else
    echo "No desktop entry found to remove. Moving on..."
fi
echo "Your menus are now free from VitalWatch."

# Step 6: Remove config file (optional)
echo "[4/6] Removing configuration file..."
if [[ -f "$CONFIG_FILE" ]]; then
    rm "$CONFIG_FILE"
    echo "Configuration file wiped clean from $CONFIG_FILE."
else
    echo "No configuration file detected. All clear!"
fi
echo "No lingering configurations to worry about."

# Step 7: Final Cleanup
echo "[5/6] Performing a final sweep..."
# Add any other cleanup tasks here
echo "System is squeaky clean!"

# Step 8: Farewell message
echo "╔════════════════════════════════════════╗"
echo "║       VitalWatch has been uninstalled! ║"
echo "║    Your system is ready for new tasks. ║"
echo "╚════════════════════════════════════════╝"

echo "Thanks for trying VitalWatch. Remember, it's always watching out for you!"
echo "Goodbye for now!"
exit 0
