from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import torch
from PIL import Image
import tempfile
import os
import cv2
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 및 프로세서 로드
processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf")
model = LlavaNextForConditionalGeneration.from_pretrained(
    "llava-hf/llava-v1.6-mistral-7b-hf",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)
model.to("cuda" if torch.cuda.is_available() else "cpu")

@app.post("/ask_video/")
async def ask_video(files: List[UploadFile] = File(...), questions: List[str] = Form(...)):
    responses = []

    if len(questions) < len(files):
        return {"error": "Each video must have at least one question."}

    for idx, file in enumerate(files):
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # 중간 프레임 추출
        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        mid_frame_idx = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame_idx)
        success, frame = cap.read()
        cap.release()
        os.remove(tmp_path)

        if not success:
            responses.append({
                "filename": file.filename,
                "error": "Failed to extract frame from video."
            })
            continue

        # 이미지 변환
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 질문 반복 처리
        for q_idx in range(len(questions)):
            question = questions[q_idx]

            # 프롬프트 구성
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": question}
                    ]
                }
            ]
            prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
            inputs = processor(prompt, image, return_tensors="pt").to(model.device)

            # 응답 생성
            with torch.no_grad():
                generate_ids = model.generate(**inputs, max_new_tokens=100)
                output = processor.decode(generate_ids[0], skip_special_tokens=True)

            responses.append({
                "filename": file.filename,
                "question": question,
                "answer": output.strip()
            })

    return {"results": responses}
