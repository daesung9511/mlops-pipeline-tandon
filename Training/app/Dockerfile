FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y tzdata ffmpeg git curl unzip jq

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

EXPOSE 5000
CMD ["bash"]
