#!/bin/bash

# Set the environment variable for the rclone container if not already set
RCLONE_CONTAINER=${RCLONE_CONTAINER:-object-persist-project25}

# Source and destination directories
SRC_DIR="$HOME/mlops-pipeline-tandon/models/whisper"
DEST_DIR="chi_tacc:$RCLONE_CONTAINER/models/whisper"

# Run the rclone copy command
rclone copy "$SRC_DIR" "$DEST_DIR" \
    --progress \
    --transfers=32 \
    --checkers=16 \
    --multi-thread-streams=4 \
    --fast-list

