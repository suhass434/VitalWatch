# Maintainer: Your Name <your.email@example.com>
pkgname=VitalWatch
pkgver=1.0.0
pkgrel=1
pkgdesc="Keep your system healthy and under watch."
arch=('any')
url="https://github.com/suhass434/VitalWatch.git"
license=('None')
depends=('python' 'python-pyqt5' 'python-yaml' 'python-pandas' 'python-joblib' 'python-scikit-learn' 'python-psutil')

source=("VitalWatch-$pkgver.tar.gz" "VitalWatch.desktop")
sha256sums=('SKIP' 'SKIP')

# Build the package
package() {
    # Create the directory structure for the installation
    mkdir -p "${pkgdir}/usr/share/VitalWatch"
    cp -r * "${pkgdir}/usr/share/VitalWatch/"
    
    # Copy the desktop entry file to the appropriate location for GUI apps
    mkdir -p "${pkgdir}/usr/share/applications"
    cp "VitalWatch.desktop" "${pkgdir}/usr/share/applications/VitalWatch.desktop"
}