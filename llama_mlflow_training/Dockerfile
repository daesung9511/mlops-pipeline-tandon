FROM pytorch/pytorch:2.1.0-cuda12.1-runtime

# Set environment variables
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /workspace
COPY train_llama.py .

# Configure git for Hugging Face (required for LLaMA-2)
ARG HF_TOKEN
RUN git config --global credential.helper store
RUN echo "machine huggingface.co login token password $HF_TOKEN" > ~/.netrc
