from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import torch
import tempfile
import os
from transformers import (
    LlavaNextVideoForConditionalGeneration,
    LlavaNextVideoProcessor
)
import logging

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로그 설정
logging.basicConfig(level=logging.INFO)

def log_model_device(model, model_name: str):
    try:
        if next(model.parameters()).is_cuda:
            logging.info(f"{model_name} is loaded on GPU: {next(model.parameters()).device}")
        else:
            logging.info(f"{model_name} is loaded on CPU")
    except StopIteration:
        logging.info(f"{model_name} has no parameters to check.")

# 모델 로딩
print("CUDA available:", torch.cuda.is_available())
print("CUDA device count:", torch.cuda.device_count())

llava_processor = LlavaNextVideoProcessor.from_pretrained("llava-hf/LLaVA-NeXT-Video-7B-hf")
llava_model = LlavaNextVideoForConditionalGeneration.from_pretrained(
    "llava-hf/LLaVA-NeXT-Video-7B-hf",
    torch_dtype=torch.float16,
    device_map="auto"
)
log_model_device(llava_model, "LLaVA-NeXT-Video Model")

# ---------------------------------------------------------------------------
# API 엔드포인트
# ---------------------------------------------------------------------------

@app.post("/ask_video/")
async def ask_video(
    files: List[UploadFile] = File(...),
    questions: List[str] = Form(...)
):
    """
    각 비디오에 대해 질문을 던지고, LLaVA-NeXT-Video를 사용하여 답변을 생성.
    """
    responses = []

    if len(questions) < len(files):
        return {"error": "Each video must have at least one question."}

    for idx, file in enumerate(files):
        # 비디오 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        question = questions[idx]
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "video", "path": tmp_path}
                ]
            }
        ]

        try:
            inputs = llava_processor.apply_chat_template(
                conversation,
                num_frames=8,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            ).to(llava_model.device)

            with torch.no_grad():
                out = llava_model.generate(**inputs, max_new_tokens=100)

            answer = llava_processor.batch_decode(out, skip_special_tokens=True)[0]
            responses.append({
                "filename": file.filename,
                "question": question,
                "answer": answer.strip()
            })
        except Exception as e:
            responses.append({
                "filename": file.filename,
                "question": question,
                "error": str(e)
            })
        finally:
            os.remove(tmp_path)

    return {"results": responses}

@app.post("/ask_video_extended/")
async def ask_video_extended(
    video: UploadFile = File(...),
    question: str = Form(...),
    transcript: Optional[UploadFile] = File(None)  # VTT 형식
):
    """
    확장 버전 엔드포인트:
    - 전사 파일이 있으면: 후보 프레임 추출 → 텍스트 유사도 + BridgeTower 평가 → 상위 후보 기반 LLaVA-NeXT-Video 응답
    - 없으면: mid-frame 추출하여 LLaVA-NeXT-Video 수행
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = os.path.join(tmp_dir, "video.mp4")
        with open(video_path, "wb") as f:
            f.write(await video.read())

        if transcript:
            # 1. 전사 저장 및 프레임 추출
            transcript_path = os.path.join(tmp_dir, "transcript.vtt")
            with open(transcript_path, "wb") as f:
                f.write(await transcript.read())

            frames_dir = os.path.join(tmp_dir, "frames")
            metas_dir = os.path.join(tmp_dir, "metas")
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(metas_dir, exist_ok=True)

            metadata_list = extract_and_save_frames_and_metadata(
                path_to_video=video_path,
                path_to_transcript=transcript_path,
                path_to_save_extracted_frames=frames_dir,
                path_to_save_metadatas=metas_dir
            )

            # 2. 텍스트 유사도 기반 후보 선정
            candidate_scores = [simple_text_similarity(question, meta['transcript']) for meta in metadata_list]
            top_indices = sorted(range(len(candidate_scores)), key=lambda i: candidate_scores[i], reverse=True)[:100]

            # 3. BridgeTower 기반 재정렬
            device = "cuda" if torch.cuda.is_available() else "cpu"
            bridge_processor = BridgeTowerProcessor.from_pretrained("BridgeTower/bridgetower-base-itm-mlm")
            bridge_model = BridgeTowerForImageAndTextRetrieval.from_pretrained("BridgeTower/bridgetower-base-itm-mlm")
            bridge_model.to(device).half()
            log_model_device(bridge_model, "BridgeTower Model")

            batch_images, batch_texts = [], []
            for i in top_indices:
                meta = metadata_list[i]
                try:
                    img = Image.open(meta['extracted_frame_path'])
                    text = f"Frame transcript: {meta['transcript']}. Query: {question}"
                    batch_images.append(img)
                    batch_texts.append(text)
                except:
                    continue

            batch = bridge_processor(batch_images, batch_texts, return_tensors="pt", padding=True, truncation=True)
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.no_grad():
                outputs = bridge_model(**batch)
            scores = outputs.logits[:, 1].tolist()
            bridge_scores = {i: s for i, s in zip(top_indices, scores)}
            top_llava_indices = sorted(bridge_scores, key=bridge_scores.get, reverse=True)[:30]
            selected_metas = [metadata_list[i] for i in top_llava_indices]

            # 4. 영상에서 해당 시점만 추려 클립 만들기
            selected_times = [meta['mid_time_ms'] for meta in selected_metas]
            selected_times = sorted(selected_times)
            logging.info(f"Selected mid times (ms): {selected_times}")

            # 영상 중 추출할 타임스탬프 기반으로 프레임 샘플링
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_indices = [int((t / 1000.0) * fps) for t in selected_times]
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sampled_frames = []

            for fi in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, min(fi, total_frames - 1))
                success, frame = cap.read()
                if success:
                    sampled_frames.append(frame)
            cap.release()

            # 5. sampled_frames → 임시 영상 저장
            sampled_path = os.path.join(tmp_dir, "selected_clip.mp4")
            if sampled_frames:
                h, w, _ = sampled_frames[0].shape
                out = cv2.VideoWriter(sampled_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                for f in sampled_frames:
                    out.write(f)
                out.release()
            else:
                sampled_path = video_path  # fallback

            # 6. LLaVA-NeXT-Video inference
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "video", "path": sampled_path}
                    ]
                }
            ]
            inputs = llava_processor.apply_chat_template(
                conversation,
                num_frames=8,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            ).to(llava_model.device)

            with torch.no_grad():
                out = llava_model.generate(**inputs, max_new_tokens=100)
            answer = llava_processor.batch_decode(out, skip_special_tokens=True)[0]

            return {
                "results": {
                    "method": "BridgeTower + LLaVA-NeXT-Video",
                    "llava_answer": answer.strip(),
                    "selected_timestamps_ms": selected_times
                }
            }

        else:
            # transcript 없을 경우 mid-frame 기반 fallback
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "video", "path": video_path}
                    ]
                }
            ]
            inputs = llava_processor.apply_chat_template(
                conversation,
                num_frames=8,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            ).to(llava_model.device)

            with torch.no_grad():
                out = llava_model.generate(**inputs, max_new_tokens=100)
            answer = llava_processor.batch_decode(out, skip_special_tokens=True)[0]

            return {
                "results": {
                    "method": "Fallback mid-frame",
                    "llava_answer": answer.strip()
                }
            }