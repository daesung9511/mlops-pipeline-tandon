import os
import tempfile
import shutil
import asyncio
import json # Added for metadata saving
from datetime import datetime # Added for metadata timestamp
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from huggingface_hub import hf_hub_download
import whisper
from llama_cpp import Llama
import boto3
import uuid

# --- MinIO Configuration and Client Initialization ---
MINIO_URL = os.environ.get('MINIO_URL') # e.g. 'http://minio:9000'
MINIO_USER = os.environ.get('MINIO_USER')
MINIO_PASSWORD = os.environ.get('MINIO_PASSWORD')
MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'production') # Default bucket

s3_client = None # Initialize S3 client globally

if MINIO_URL and MINIO_USER and MINIO_PASSWORD:
    try:
        print("Initializing MinIO S3 client...")
        s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_URL,
            aws_access_key_id=MINIO_USER,
            aws_secret_access_key=MINIO_PASSWORD,
            region_name='us-east-1'
        )

        if s3_client: # Check if client was successfully initialized and bucket check/create passed
             print("MinIO S3 client initialized successfully.")

    except Exception as e:
        print(f"Error initializing MinIO S3 client: {e}")
        s3_client = None # Ensure client is None if initialization fails
else:
    print("MinIO environment variables (MINIO_URL, MINIO_USER, MINIO_PASSWORD) not fully set. S3 client not initialized. Data will NOT be saved to MinIO.")


# --- Configuration ---
# Choose a Whisper model size (e.g., 'base', 'small', 'medium', 'large')
WHISPER_MODEL_SIZE = "base"

# --- Hugging Face Llama Model Configuration ---
# These are placeholders and will be replaced with trained model paths
# Replace with the repo ID and filename of the GGUF model you want to use from Hugging Face
# You can find GGUF models from users like 'TheBloke'
HF_REPO_ID = "TheBloke/Llama-2-7B-Chat-GGUF" # Example: Llama-2 7B Chat model
HF_FILE_NAME = "llama-2-7b-chat.Q4_K_M.gguf" # Example: A specific quantized GGUF file

# --- Initialize Models ---
# Load models globally on application startup with error handling
whisper_model = None
llm = None
llama_model_path_cached = None # To store the path where the model is cached

try:
    print(f"Loading Whisper model: {WHISPER_MODEL_SIZE}...")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    print("Whisper model loaded.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    # Handle this error in the endpoint (already have checks there)

try:
    print(f"Attempting to download Llama model '{HF_FILE_NAME}' from '{HF_REPO_ID}'...")
    # hf_hub_download caches the model, subsequent calls are fast
    llama_model_path_cached = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=HF_FILE_NAME
    )
    print(f"Llama model downloaded/cached to: {llama_model_path_cached}")

    print("Loading Llama model...")
    # n_gpu_layers, n_ctx, etc. - adjust based on your model and hardware
    llm = Llama(
        model_path=llama_model_path_cached, # Use the cached path
        n_gpu_layers=999, # Set > 0 if we use GPU
        n_ctx=4096, # context window size (FIXME: MIGHT BE TOO SMALL)
        verbose=False
    )
    print("Llama model loaded.")
except Exception as e:
    print(f"Error downloading or loading Llama model: {e}")
    llm = None # Set to None if loading fails


# --- FastAPI App ---
app = FastAPI(
    title="Vizario: Meeting Summarization and Q&A",
    description="API to process meeting audio using Whisper for transcription and Llama for summarization or question answering.",
    version="0.1.0"
)

# --- Define Response Models using Pydantic ---
class BaseMeetingResponse(BaseModel):
    filename: str = Field(..., description="The name of the uploaded audio file.")
    transcript: str = Field(..., description="The generated transcript from the audio.")
    processing_task: str = Field(..., description="Indicates if summarization or Q&A was performed.")

class MeetingSummaryResponse(BaseMeetingResponse):
     summary: str = Field(..., description="The generated summary of the meeting transcript.")

class MeetingQAResponse(BaseMeetingResponse):
     query: str = Field(..., description="The user's question about the transcript.")
     answer: str = Field(..., description="The answer to the query based on the transcript.")

class FeedbackRequest(BaseModel):   # Define Request Model for Feedback 
    interaction_id: str = Field(..., description="The unique ID of the interaction being rated.")
    helpful: bool = Field(..., description="Whether the response was helpful (True) or unhelpful (False).")
    feedback_text: str | None = Field(None, description="Optional text feedback from the user.")

# --- Helper Functions for MinIO Saving ---
async def save_audio_to_minio(s3_client, bucket_name: str, object_key: str, file_path: str, content_type: str):
    """Saves the temporary audio file to MinIO."""
    if not s3_client:
        print(f"MinIO client not available. Skipping audio save for key: {object_key}")
        return
    try:
        loop = asyncio.get_event_loop()
        with open(file_path, 'rb') as f_audio:
             await loop.run_in_executor( # Run blocking S3 upload in executor
                  None, # Use default executor
                  lambda: s3_client.upload_fileobj(
                       f_audio,
                       bucket_name,
                       object_key,
                       ExtraArgs={'ContentType': content_type or 'application/octet-stream'}
                  )
             )
        print(f"Successfully uploaded audio file to MinIO: {object_key}")
    except Exception as e:
        print(f"Error saving audio file to MinIO key {object_key}: {e}")

async def save_text_to_minio(s3_client, bucket_name: str, object_key: str, text_content: str, content_type: str = 'text/plain'):
    """Saves text content (transcript, summary/answer) to MinIO."""
    if not s3_client:
        print(f"MinIO client not available. Skipping text save for key: {object_key}")
        return
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor( # Run blocking S3 put_object in executor
             None, # Use default executor
             lambda: s3_client.put_object(
                  Bucket=bucket_name,
                  Key=object_key,
                  Body=text_content.encode('utf-8'), # Encode text to bytes
                  ContentType=content_type
             )
        )
        print(f"Successfully uploaded text to MinIO: {object_key}")
    except Exception as e:
        print(f"Error saving text to MinIO key {object_key}: {e}")

async def save_metadata_to_minio(s3_client, bucket_name: str, object_key: str, metadata: dict):
    """Saves metadata dictionary as JSON to MinIO."""
    if not s3_client:
        print(f"MinIO client not available. Skipping metadata save for key: {object_key}")
        return
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor( # Run blocking S3 put_object in executor
            None, # Use default executor
            lambda: s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=json.dumps(metadata, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
        )
        print(f"Successfully uploaded metadata to MinIO: {object_key}")
    except Exception as e:
        print(f"Error saving metadata to MinIO key {object_key}: {e}")


# --- Endpoint ---

@app.post(
    "/process-meeting/",
    response_model=MeetingSummaryResponse | MeetingQAResponse,
    responses={500: {"description": "Internal Server Error"}}
)
async def process_meeting_audio(
    audio_file: UploadFile = File(...),
    query: str = Form(None)
):
    """
    Processes an uploaded audio file to generate a transcript using Whisper
    and then either summarizes the transcript or answers a question using Llama.
    Saves results and original audio to MinIO in the background.

    Args:
        audio_file (UploadFile): The meeting audio file (e.g., .wav, .mp3, .m4a).
        query (str, optional): A question to ask about the meeting transcript.
                                If provided, performs Q&A. If None, performs summarization.

    Returns:
        MeetingSummaryResponse | MeetingQAResponse: The response containing transcript and summary or answer.
    """
    # Check if models were loaded successfully on startup
    if not whisper_model:
        raise HTTPException(status_code=500, detail="Whisper model failed to load on startup.")
    if not llm:
         raise HTTPException(status_code=500, detail=f"Llama model failed to load on startup. Check HF_REPO_ID '{HF_REPO_ID}' and HF_FILE_NAME '{HF_FILE_NAME}'.")

    # --- Save uploaded audio to a temporary file ---
    temp_audio_file = None # Declare before try block
    try:
        print(f"Saving uploaded file {audio_file.filename} temporarily...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio_file.read()
            tmp.write(content)
            temp_audio_file = tmp.name
        print(f"Saved temporarily to: {temp_audio_file}")


        # --- Transcribe with Whisper ---
        print(f"Transcribing {audio_file.filename}...")
        loop = asyncio.get_event_loop()
        transcript_result = await loop.run_in_executor(
            None, whisper_model.transcribe, temp_audio_file
        )
        transcript_text = transcript_result["text"]
        print("Transcription complete.")

        # --- Process with Llama (Summarization or Q&A) ---
        llama_output = None
        result_text = ""
        processing_task = "Summarization" # Default task

        if query:
            processing_task = "Question Answering"
            print(f"Performing Q&A with query: '{query}'")
            prompt = f"""Based on the following meeting transcript, answer the question concisely:

Transcript:
{transcript_text}

Question: {query}
Answer:"""
            llama_output = await loop.run_in_executor(
                None,
                lambda: llm(prompt, max_tokens=256, stop=["\n", "Question:"], temperature=0.1)
            )
            result_text = llama_output["choices"][0]["text"].strip()

        else: # No query, perform summarization
            processing_task = "Summarization" # Ensure it's set consistently
            print("Performing summarization.")
            prompt = f"""Summarize the following meeting transcript, highlighting key topics and decisions:

Transcript:
{transcript_text}

Summary:"""
            llama_output = await loop.run_in_executor(
                None,
                lambda: llm(prompt, max_tokens=512, stop=["\nTranscript:"], temperature=0.7)
            )
            result_text = llama_output["choices"][0]["text"].strip()


        # --- Initiate Data Saving to MinIO (NEW - as background tasks) ---
        # Check if the s3_client was successfully initialized globally
        if s3_client:
             processing_uuid = str(uuid.uuid4()) # Generate a unique ID for this processing event
             base_filename = os.path.splitext(audio_file.filename)[0] # Get filename without extension

             # Define object keys
             audio_object_key = f"audio/{processing_uuid}/{base_filename}{os.path.splitext(audio_file.filename)[1]}"
             transcript_object_key = f"transcripts/{processing_uuid}/{base_filename}.txt"
             output_type_dir = "answers" if query else "summaries"
             output_object_key = f"{output_type_dir}/{processing_uuid}/{base_filename}_output.txt"
             metadata_object_key = f"metadata/{processing_uuid}/metadata.json"

             # Prepare metadata
             metadata = {
                 "processing_uuid": processing_uuid,
                 "original_filename": audio_file.filename,
                 "query": query,
                 "processing_task": processing_task,
                 "audio_s3_key": audio_object_key,
                 "transcript_s3_key": transcript_object_key,
                 "output_s3_key": output_object_key,
                 "timestamp_utc": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
             }

             # Create background tasks for saving. These will run concurrently.
             # Use asyncio.create_task to run these without blocking the endpoint response.
             asyncio.create_task(save_audio_to_minio(s3_client, MINIO_BUCKET_NAME, audio_object_key, temp_audio_file, audio_file.content_type))
             asyncio.create_task(save_text_to_minio(s3_client, MINIO_BUCKET_NAME, transcript_object_key, transcript_text))
             asyncio.create_task(save_text_to_minio(s3_client, MINIO_BUCKET_NAME, output_object_key, result_text))
             asyncio.create_task(save_metadata_to_minio(s3_client, MINIO_BUCKET_NAME, metadata_object_key, metadata))

             print(f"Initiated background saves for processing_uuid: {processing_uuid}")

        else:
             print("MinIO client not initialized. Skipping data save to MinIO.")


        # --- Return Response ---
        # The endpoint returns immediately after initiating background tasks
        if query:
            return MeetingQAResponse(
                filename=audio_file.filename,
                transcript=transcript_text,
                processing_task=processing_task,
                query=query,
                answer=result_text
            )
        else:
             return MeetingSummaryResponse(
                filename=audio_file.filename,
                transcript=transcript_text,
                processing_task=processing_task,
                summary=result_text
            )

    except Exception as e:
        print(f"An error occurred during processing: {e}")
        # Ensure temp file cleanup even if an error occurs before finally
        if temp_audio_file and os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
            print(f"Cleaned up temporary file after error: {temp_audio_file}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {e}")
    finally:
        # --- Clean up temporary file ---
        # TODO: not safe, might have a race condition with minIO; consider adding delay
        if temp_audio_file and os.path.exists(temp_audio_file):
             print(f"Processing complete. Temporary file {temp_audio_file} will be cleaned up by finally block.")
             os.remove(temp_audio_file)