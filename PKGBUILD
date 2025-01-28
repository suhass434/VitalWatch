# Maintainer: Your Name <your.email@example.com>
pkgname=VitalWatch
pkgver=1.0.0
pkgrel=1
pkgdesc="Keep your system healthy and under watch."
arch=('any')
url="https://github.com/suhass434/VitalWatch.git"
license=('None')
depends=('python' 'python-virtualenv')
source=("VitalWatch-$pkgver.tar.gz" "VitalWatch.desktop")
sha256sums=('SKIP' 'SKIP')

package() {
    # Create the directory structure for the application
    mkdir -p "${pkgdir}/usr/share/VitalWatch"
    mkdir -p "${pkgdir}/usr/share/applications"
    mkdir -p "${pkgdir}/usr/bin"

    # Set up a Python virtual environment in the application directory
    python -m venv "${pkgdir}/usr/share/VitalWatch/venv"

    # Activate the virtual environment and install dependencies
    source "${pkgdir}/usr/share/VitalWatch/venv/bin/activate"
    pip install --no-cache-dir -r requirements.txt
    deactivate

    # Copy application files into the installation directory
    cp -r ./* "${pkgdir}/usr/share/VitalWatch/"
    
    # Create a wrapper script to activate the virtual environment and run the application
    cat << EOF > "${pkgdir}/usr/bin/VitalWatch"
#!/bin/bash
source /usr/share/VitalWatch/venv/bin/activate
python /usr/share/VitalWatch/run.py
EOF
    chmod +x "${pkgdir}/usr/bin/VitalWatch"

    # Place the desktop file in the appropriate directory
    cp "VitalWatch.desktop" "${pkgdir}/usr/share/applications/VitalWatch.desktop"
}
