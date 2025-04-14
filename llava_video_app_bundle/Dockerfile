FROM python:3.10-slim
WORKDIR /app

# Install system libraries needed by opencv and others.
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

# Copy your requirements and install them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force-install the CUDA-enabled PyTorch wheels.
# (The example here uses cu118; adjust based on your host and preferred PyTorch build.)
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

COPY . .
CMD ["uvicorn", "llava_video_app:app", "--host", "0.0.0.0", "--port", "8000"]
