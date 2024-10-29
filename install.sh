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