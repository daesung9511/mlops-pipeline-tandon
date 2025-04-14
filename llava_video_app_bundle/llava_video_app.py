from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import torch
import tempfile
import os
import cv2
import json
from PIL import Image
import math
import webvtt  # pip install webvtt-py
from transformers import (
    LlavaNextProcessor, 
    LlavaNextForConditionalGeneration,
    BridgeTowerProcessor, 
    BridgeTowerForImageAndTextRetrieval
)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Llava model and processor
llava_processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf")
llava_model = LlavaNextForConditionalGeneration.from_pretrained(
    "llava-hf/llava-v1.6-mistral-7b-hf",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)
llava_model.to("cuda" if torch.cuda.is_available() else "cpu")

# ---------------------------------------------------------------------------
# Helper functions used in the extended pipeline
# ---------------------------------------------------------------------------

def str2time(strtime: str) -> float:
    """Convert a transcript time string (e.g. '00:01:23.456') into milliseconds."""
    strtime = strtime.strip('"')
    # Split into hours, minutes, seconds (which can include decimals)
    hrs, mins, secs = [float(c) for c in strtime.split(':')]
    total_seconds = hrs * 3600 + mins * 60 + secs
    return total_seconds * 1000

def maintain_aspect_ratio_resize(image, width: Optional[int] = None, height: Optional[int] = None, inter=cv2.INTER_AREA):
    """Resize an image and maintain its aspect ratio."""
    h, w = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    return cv2.resize(image, dim, interpolation=inter)

def extract_and_save_frames_and_metadata(
    path_to_video: str,
    path_to_transcript: str,
    path_to_save_extracted_frames: str,
    path_to_save_metadatas: str
):
    """Extract frames from video segments based on a VTT transcript.
       Saves each extracted frame and returns metadata for each frame.
    """
    metadatas = []

    video = cv2.VideoCapture(path_to_video)
    trans = webvtt.read(path_to_transcript)

    for idx, caption in enumerate(trans):
        start_time_ms = str2time(caption.start)
        end_time_ms = str2time(caption.end)
        mid_time_ms = (start_time_ms + end_time_ms) / 2
        text = caption.text.replace("\n", " ")
        video.set(cv2.CAP_PROP_POS_MSEC, mid_time_ms)
        success, frame = video.read()
        if success:
            # Resize image as needed (here height is set to 350 for consistency)
            image = maintain_aspect_ratio_resize(frame, height=350)
            img_fname = f'frame_{idx}.jpg'
            img_fpath = os.path.join(path_to_save_extracted_frames, img_fname)
            cv2.imwrite(img_fpath, image)
            metadata = {
                'extracted_frame_path': img_fpath,
                'transcript': text,
                'video_segment_id': idx,
                'video_path': path_to_video,
                'mid_time_ms': mid_time_ms,
            }
            metadatas.append(metadata)
        else:
            print(f"ERROR! Cannot extract frame at index {idx}")
    
    # Save metadata to disk
    metadata_file = os.path.join(path_to_save_metadatas, 'metadatas.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadatas, f)
    
    video.release()
    return metadatas

def simple_text_similarity(text_a: str, text_b: str) -> int:
    """Compute a simple similarity score based on word overlap."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    return len(words_a.intersection(words_b))

def create_image_collage(images: List[Image.Image], columns: int = 3, thumbnail_height: int = 150) -> Image.Image:
    """
    Create a collage from a list of images.
    Resizes each image to a thumbnail (keeping aspect ratio) and arranges them in a grid.
    """
    if not images:
        raise ValueError("No images provided for collage creation.")

    # Resize images to a common thumbnail height while maintaining aspect ratio
    thumbs = []
    thumb_widths = []
    for img in images:
        aspect = img.width / img.height
        thumb_w = int(thumbnail_height * aspect)
        thumb = img.resize((thumb_w, thumbnail_height))
        thumbs.append(thumb)
        thumb_widths.append(thumb_w)
    
    rows = math.ceil(len(thumbs) / columns)
    # Determine maximum width per column
    max_col_widths = [0] * columns
    for i, thumb in enumerate(thumbs):
        col = i % columns
        if thumb.width > max_col_widths[col]:
            max_col_widths[col] = thumb.width

    collage_width = sum(max_col_widths)
    collage_height = thumbnail_height * rows

    collage = Image.new('RGB', (collage_width, collage_height), color=(255, 255, 255))
    x_offset = 0
    y_offset = 0
    col = 0
    for idx, thumb in enumerate(thumbs):
        collage.paste(thumb, (x_offset, y_offset))
        x_offset += max_col_widths[col]
        col += 1
        if col == columns:
            col = 0
            x_offset = 0
            y_offset += thumbnail_height
    return collage

# ---------------------------------------------------------------------------
# Main API Endpoints
# ---------------------------------------------------------------------------

@app.post("/ask_video/")
async def ask_video(
    files: List[UploadFile] = File(...),
    questions: List[str] = Form(...)
):
    """
    Original endpoint: For each video, extract a single mid-frame and run Llava on each question.
    """
    responses = []
    if len(questions) < len(files):
        return {"error": "Each video must have at least one question."}
    for idx, file in enumerate(files):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

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

        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        # Process each question with Llava
        for question in questions:
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": question}
                    ]
                }
            ]
            prompt = llava_processor.apply_chat_template(conversation, add_generation_prompt=True)
            inputs = llava_processor(prompt, image, return_tensors="pt").to(llava_model.device)
            with torch.no_grad():
                generate_ids = llava_model.generate(**inputs, max_new_tokens=100)
                output = llava_processor.decode(generate_ids[0], skip_special_tokens=True)
            responses.append({
                "filename": file.filename,
                "question": question,
                "answer": output.strip()
            })
    return {"results": responses}

@app.post("/ask_video_extended/")
async def ask_video_extended(
    video: UploadFile = File(...),
    question: str = Form(...),
    transcript: Optional[UploadFile] = File(None)  # Expected in VTT format
):
    """
    Extended endpoint:
    If a transcript file is provided, the flow is:
      Data (video + transcript) →
      Frame extraction + metadata building →
      Candidate selection via simple text similarity and BridgeTower evaluation →
      Assemble candidate information and create a collage image →
      Build a detailed prompt for Llava →
      Llava inference and return the answer.
    
    If transcript is not provided, falls back to extracting a single mid-frame and Llava inference.
    """
    # Create temporary directories for storing video, transcript, frames, and metadata
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = os.path.join(tmp_dir, "video.mp4")
        with open(video_path, "wb") as f:
            f.write(await video.read())

        if transcript is not None:
            transcript_path = os.path.join(tmp_dir, "transcript.vtt")
            with open(transcript_path, "wb") as f:
                f.write(await transcript.read())

            # Create sub-directories for frames and metadatas
            frames_dir = os.path.join(tmp_dir, "extracted_frames")
            metas_dir = os.path.join(tmp_dir, "metadatas")
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(metas_dir, exist_ok=True)

            # Extract candidate frames and build metadata list from transcript segments
            metadata_list = extract_and_save_frames_and_metadata(
                path_to_video=video_path,
                path_to_transcript=transcript_path,
                path_to_save_extracted_frames=frames_dir,
                path_to_save_metadatas=metas_dir
            )

            # -------------------------------
            # 1. Candidate filtering via simple text similarity
            candidate_scores = [simple_text_similarity(question, meta['transcript']) for meta in metadata_list]
            top_candidate_indices = sorted(
                range(len(candidate_scores)), key=lambda i: candidate_scores[i], reverse=True
            )[:100]

            # -------------------------------
            # 2. Re-evaluate top candidates using BridgeTower
            device = "cuda" if torch.cuda.is_available() else "cpu"
            bridge_processor = BridgeTowerProcessor.from_pretrained("BridgeTower/bridgetower-base-itm-mlm")
            bridge_model = BridgeTowerForImageAndTextRetrieval.from_pretrained("BridgeTower/bridgetower-base-itm-mlm")
            bridge_model.to(device)
            bridge_model = bridge_model.half()  # Use half precision to reduce memory usage

            batch_images = []
            batch_texts = []
            for idx in top_candidate_indices:
                meta = metadata_list[idx]
                try:
                    frame_image = Image.open(meta['extracted_frame_path'])
                except Exception as e:
                    continue
                candidate_text = f"Frame transcript: {meta['transcript']}. Query: {question}"
                batch_images.append(frame_image)
                batch_texts.append(candidate_text)

            # Process candidates in batch (if not too many)
            batch_encoding = bridge_processor(batch_images, batch_texts, return_tensors="pt", padding=True, truncation=True)
            batch_encoding = {key: tensor.to(device) for key, tensor in batch_encoding.items()}
            with torch.no_grad():
                outputs = bridge_model(**batch_encoding)
            # Use the second logit score for ranking
            batch_scores = outputs.logits[:, 1].tolist()
            # Map candidate index to BridgeTower score
            bridge_scores = {idx: score for idx, score in zip(top_candidate_indices, batch_scores)}
            top_llava_candidate_indices = sorted(bridge_scores, key=bridge_scores.get, reverse=True)[:30]
            selected_candidates = [metadata_list[i] for i in top_llava_candidate_indices]

            # -------------------------------
            # 3. Build candidate info and create a collage from selected frames
            candidate_info_str = ""
            candidate_images = []
            for idx, candidate in enumerate(selected_candidates):
                candidate_info_str += (
                    f"Candidate {idx+1}:\n"
                    f"  - Frame path: {candidate['extracted_frame_path']}\n"
                    f"  - Transcript: {candidate['transcript']}\n"
                    f"  - Video segment ID: {candidate['video_segment_id']} at {candidate['mid_time_ms']}ms\n\n"
                )
                try:
                    candidate_images.append(Image.open(candidate['extracted_frame_path']))
                except Exception as e:
                    continue

            # Create a collage image from candidate images (if any)
            if candidate_images:
                collage_image = create_image_collage(candidate_images, columns=3, thumbnail_height=150)
            else:
                # Fallback: use the mid-frame from the video (if no candidates available)
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                mid_frame_idx = total_frames // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame_idx)
                success, frame = cap.read()
                cap.release()
                if success:
                    collage_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                else:
                    return {"error": "Failed to extract image from video."}

            # -------------------------------
            # 4. Create Llava prompt that integrates candidate info
            llava_prompt = (
                f"User prompt: {question}\n\n"
                f"Selected candidate frame info (total {len(selected_candidates)} candidates):\n"
                f"{candidate_info_str}\n"
                "Based on the above, provide a detailed analysis and explanation of the scenes relevant to the query."
            )

            # -------------------------------
            # 5. Run Llava inference with the constructed prompt and collage image
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": llava_prompt}
                    ]
                }
            ]
            prompt_text = llava_processor.apply_chat_template(conversation, add_generation_prompt=True)
            inputs = llava_processor(prompt_text, collage_image, return_tensors="pt").to(llava_model.device)
            with torch.no_grad():
                generate_ids = llava_model.generate(**inputs, max_new_tokens=100)
                output = llava_processor.decode(generate_ids[0], skip_special_tokens=True)

            result = {
                "method": "BridgeTower-LLaVA flow",
                "llava_answer": output.strip(),
                "candidate_info": candidate_info_str
            }
            return {"results": result}
        else:
            # Fallback to original behavior if no transcript provided
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            mid_frame_idx = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame_idx)
            success, frame = cap.read()
            cap.release()
            if not success:
                return {"error": "Failed to extract frame from video."}
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": question}
                    ]
                }
            ]
            prompt = llava_processor.apply_chat_template(conversation, add_generation_prompt=True)
            inputs = llava_processor(prompt, image, return_tensors="pt").to(llava_model.device)
            with torch.no_grad():
                generate_ids = llava_model.generate(**inputs, max_new_tokens=100)
                output = llava_processor.decode(generate_ids[0], skip_special_tokens=True)
            return {"results": {"method": "Fallback mid-frame", "llava_answer": output.strip()}}

