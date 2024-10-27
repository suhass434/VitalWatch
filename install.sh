#!/bin/bash

python -m venv ~/.local/share/system-monitor/venv

source ~/.local/share/system-monitor/venv/bin/activate

pip install -r requirements.txt

mkdir -p ~/.local/share/system-monitor/app
cp -r app/* ~/.local/share/system-monitor/app/
cp run.py ~/.local/share/system-monitor/

mkdir -p ~/.local/share/applications
cp system-monitor.desktop ~/.local/share/applications/

chmod +x ~/.local/share/system-monitor/run.py