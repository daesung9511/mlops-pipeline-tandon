#!/usr/bin/env bash

# Usage example
# ./mount_chi_tacc.sh -i YOUR_APP_CRED_ID -s YOUR_APP_CRED_SECRET -u YOUR_USER_ID

set -e

# Usage function
usage() {
    echo "Usage: $0 [-i APP_CRED_ID] [-s APP_CRED_SECRET] [-f CRED_FILE] [-u USER_ID] [-c CONTAINER] [-m MOUNT_DIR]"
    echo "  -i APP_CRED_ID         Application Credential ID"
    echo "  -s APP_CRED_SECRET     Application Credential Secret"
    echo "  -f CRED_FILE           File containing 'application_credential_id' and 'application_credential_secret' lines"
    echo "  -u USER_ID             User ID for Swift authentication"
    echo "  -c CONTAINER           Object storage container name (default: object-persist-project25)"
    echo "  -m MOUNT_DIR           Local mount directory (default: ~/mnt)"
    exit 1
}

# Defaults
CONTAINER="object-persist-project25"
MOUNT_DIR="$HOME/mnt"
USER_ID="YOUR_USER_ID"

# Parse arguments
while getopts "i:s:f:u:c:m:" opt; do
    case $opt in
        i) APP_CRED_ID="$OPTARG" ;;
        s) APP_CRED_SECRET="$OPTARG" ;;
        f) CRED_FILE="$OPTARG" ;;
        u) USER_ID="$OPTARG" ;;
        c) CONTAINER="$OPTARG" ;;
        m) MOUNT_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

# Validate input
if [[ -n "$CRED_FILE" ]]; then
    if [[ ! -f "$CRED_FILE" ]]; then
        echo "Credential file not found: $CRED_FILE"
        exit 1
    fi
    APP_CRED_ID=$(grep -m1 application_credential_id "$CRED_FILE" | awk -F'=' '{print $2}' | xargs)
    APP_CRED_SECRET=$(grep -m1 application_credential_secret "$CRED_FILE" | awk -F'=' '{print $2}' | xargs)
    if [[ -z "$APP_CRED_ID" || -z "$APP_CRED_SECRET" ]]; then
        echo "Credential file missing required fields."
        exit 1
    fi
elif [[ -z "$APP_CRED_ID" || -z "$APP_CRED_SECRET" ]]; then
    echo "Must provide either -i and -s, or -f."
    usage
fi

# Download and install rclone if not present
if ! command -v rclone &> /dev/null; then
    echo "Installing rclone..."
    curl https://rclone.org/install.sh | sudo bash
fi

# Ensure user_allow_other is set in /etc/fuse.conf
sudo sed -i '/^#user_allow_other/s/^#//' /etc/fuse.conf

# Prepare rclone config directory
mkdir -p "$HOME/.config/rclone"

# Write rclone config
cat > "$HOME/.config/rclone/rclone.conf" <<EOF
[chi_tacc]
type = swift
user_id = $USER_ID
application_credential_id = $APP_CRED_ID
application_credential_secret = $APP_CRED_SECRET
auth = https://chi.tacc.chameleoncloud.org:5000/v3
region = CHI@TACC
EOF

# Test rclone config
echo "Testing rclone connection..."
rclone lsd chi_tacc: || { echo "rclone test failed"; exit 1; }

# Set environment variable for container
export RCLONE_CONTAINER="$CONTAINER"

# Create and set permissions for mount directory
sudo mkdir -p "$MOUNT_DIR"
sudo chown -R "$USER" "$MOUNT_DIR"
sudo chgrp -R "$USER" "$MOUNT_DIR"

# Mount the remote storage
echo "Mounting remote storage..."
rclone mount "chi_tacc:$CONTAINER" "$MOUNT_DIR" --read-only --allow-other --daemon

echo "Mount complete: $MOUNT_DIR"
