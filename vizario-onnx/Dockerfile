# Use an official Python runtime as a base image
# Consider a base image with CUDA pre-installed if using onnxruntime-gpu
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    ffmpeg \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Pre-downloads Whisper Model (Saves time on first run) ---
ARG WHISPER_MODEL_SIZE="base"
RUN python -c "import whisper; model_size = '$WHISPER_MODEL_SIZE'; print(f'Downloading Whisper model: {model_size}'); whisper.load_model(model_size); print('Download complete.')"

# Copy the application code into the working directory
COPY app.py .

# Make the FastAPI application available on port 8000
EXPOSE 8000

# Command to run the application
# The ONNX model will be accessed via a volume mount at /root/models/onnx
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]