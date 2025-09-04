#!/bin/bash

#  Log Analysis Application - Release Packaging Script
# Creates a distribution package for easy deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
 echo -e "${GREEN} $1${NC}"
}

print_info() {
 echo -e "${BLUE} $1${NC}"
}

print_error() {
 echo -e "${RED} $1${NC}"
}

# Get version from command line or default
VERSION=${1:-"v1.0"}
PACKAGE_NAME="log-analyzer-${VERSION}"

echo " Creating Log Analysis Application Release Package"
echo "=================================================="
print_info "Version: $VERSION"
print_info "Package: $PACKAGE_NAME.tar.gz"
echo ""

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$PACKAGE_NAME"

print_info "Creating package directory: $PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy essential files
print_status "Copying application files..."

# Core application
cp -r backend "$PACKAGE_DIR/"
cp -r frontend "$PACKAGE_DIR/"

# Configuration and deployment
cp docker-compose.yml "$PACKAGE_DIR/"
cp deploy.sh "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"
cp DEPLOYMENT.md "$PACKAGE_DIR/"

# Create a simple installer script for end users
cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash

echo " Installing Log Analysis Application..."
echo "======================================="

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh

echo ""
echo " Installation complete!"
echo "Open http://localhost:3000 to start analyzing logs!"
EOF

chmod +x "$PACKAGE_DIR/install.sh"

# Clean up unnecessary files
print_info "Cleaning up development files..."

# Remove backend development files
rm -rf "$PACKAGE_DIR/backend/venv"
rm -rf "$PACKAGE_DIR/backend/__pycache__"
rm -rf "$PACKAGE_DIR/backend/.pytest_cache"
find "$PACKAGE_DIR/backend" -name "*.pyc" -delete
find "$PACKAGE_DIR/backend" -name "__pycache__" -delete

# Remove frontend development files
rm -rf "$PACKAGE_DIR/frontend/node_modules"
rm -rf "$PACKAGE_DIR/frontend/.next"
rm -rf "$PACKAGE_DIR/frontend/dist"
rm -f "$PACKAGE_DIR/frontend/.env"

# Create a simple requirements file for the package
cat > "$PACKAGE_DIR/REQUIREMENTS.txt" << 'EOF'
System Requirements:
==================
- Docker and Docker Compose
- 4GB+ RAM (8GB+ recommended)
- 10GB+ free disk space
- Internet connection (for initial setup)

Supported Operating Systems:
==========================
- Linux (Ubuntu 20.04+, CentOS 8+, etc.)
- macOS (10.15+)
- Windows 10+ with WSL2

Installation:
============
1. Extract this package: tar -xzf log-analyzer-v1.0.tar.gz
2. Run installer: cd log-analyzer-v1.0 && ./install.sh
3. Open browser: http://localhost:3000

Support:
=======
- Documentation: README.md and DEPLOYMENT.md
- Issues: https://github.com/your-repo/loganalysis/issues
EOF

# Create version info
cat > "$PACKAGE_DIR/VERSION" << EOF
Log Analysis Application
Version: $VERSION
Build Date: $(date)
Components:
- Frontend: React + TypeScript
- Backend: FastAPI + Python
- AI: CodeLlama 13B via Ollama
EOF

# Create tarball
print_info "Creating release package..."
cd "$TEMP_DIR"
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"

# Move to current directory
mv "${PACKAGE_NAME}.tar.gz" "$(pwd)/../${PACKAGE_NAME}.tar.gz"
FINAL_PATH="$(pwd)/../${PACKAGE_NAME}.tar.gz"

# Cleanup
rm -rf "$TEMP_DIR"

# Calculate size and checksum
FILE_SIZE=$(du -h "$FINAL_PATH" | cut -f1)
CHECKSUM=$(shasum -a 256 "$FINAL_PATH" | cut -d' ' -f1)

print_status "Package created successfully!"
echo ""
echo " Release Package Details:"
echo "=========================="
echo "• File: $FINAL_PATH"
echo "• Size: $FILE_SIZE"
echo "• SHA256: $CHECKSUM"
echo ""

echo " Distribution Instructions:"
echo "============================="
echo "1. Share the package file: ${PACKAGE_NAME}.tar.gz"
echo "2. Users extract with: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. Users run: cd $PACKAGE_NAME && ./install.sh"
echo "4. Application available at: http://localhost:3000"
echo ""

print_status " Release package ready for distribution!"
echo ""

# Optionally create a quick test
read -p "Test the package locally? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
 print_info "Testing package extraction..."
 TEST_DIR=$(mktemp -d)
 cd "$TEST_DIR"
 tar -xzf "$FINAL_PATH"
 cd "$PACKAGE_NAME"
 ls -la
 print_status "Package extraction test successful!"
 rm -rf "$TEST_DIR"
fi