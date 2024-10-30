#!/bin/bash

# mkdir -p ~/.local/share/AutoGuard

# python -m venv ~/.local/share/AutoGuard/venv

# source ~/.local/share/AutoGuard/venv/bin/activate.fish

# pip install -r requirements.txt

# mkdir -p ~/.local/share/system-monitor/app
# cp -r app/* ~/.local/share/system-monitor/app/
# cp run.py ~/.local/share/system-monitor/

# cp AutoGuard.desktop ~/.local/share/applications/

# chmod +x ~/.local/share/AutoGuard.desktop/run.py

# echo "Installation completed successfully."

# python run.py



# Check if the current shell is fish
if [ "$SHELL" != "/usr/bin/bash" ] || [ "$SHELL" != "/bin/bash" ]; then
    echo "Switching to bash to avoid fish shell issues..."
    exec bash "$0"  # Restart this script in bash
fi

python -m venv env
source env/bin/activate

pip install -r requirements.txt

# mkdir -p ~/.local/share/system-monitor/app
# cp -r app/* ~/.local/share/system-monitor/app/
# cp run.py ~/.local/share/system-monitor/

cp AutoGuard.desktop ~/.local/share/applications/

chmod +x run.py

echo "Installation completed successfully."

python run.py