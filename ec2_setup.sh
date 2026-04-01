#!/usr/bin/env bash
# ============================================================
# EC2 First-Time Setup Script
# Run this ONCE manually after launching EC2 instance.
# Ubuntu 22.04 LTS assumed.
# Usage:  bash ec2_setup.sh
# ============================================================
set -e

echo "======================================"
echo " CloudTask — EC2 First-Time Setup"
echo "======================================"

# ── 1. Update system packages ──────────────────────────────
echo "[1/7] Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# ── 2. Install Python 3, pip, venv and git ─────────────────
echo "[2/7] Installing Python 3, pip, venv, git..."
sudo apt-get install -y python3 python3-pip python3-venv git

# ── 3. Clone the repository ────────────────────────────────
echo "[3/7] Cloning the CloudTask repository..."
cd /home/ubuntu
# Replace the URL below with actual GitHub repo URL
git clone https://github.com/kakshitha944-dev/cloudtask-app.git
cd cloudtask

# ── 4. Create virtual environment and install dependencies ─
echo "[4/7] Creating Python venv and installing requirements..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 5. Create log directory ────────────────────────────────
echo "[5/7] Creating log directory..."
mkdir -p /home/ubuntu/cloudtask/logs

# ── 6. Install and enable the systemd service ──────────────
echo "[6/7] Installing systemd service for Gunicorn..."
sudo cp cloudtask.service /etc/systemd/system/cloudtask.service
sudo systemctl daemon-reload
sudo systemctl enable cloudtask
sudo systemctl start cloudtask

# ── 7. Check service status ────────────────────────────────
echo "[7/7] Checking service status..."
sudo systemctl status cloudtask --no-pager

echo ""
echo "======================================"
echo " Setup complete!"
echo " App is running at http://$(curl -s ifconfig.me):5000"
echo " IMPORTANT: Open port 5000 in EC2 Security Group!"
echo "======================================"
