import os
import tempfile
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
# Import hf_hub_download
from huggingface_hub import hf_hub_download # Corrected import

import whisper
from llama_cpp import Llama

# --- Configuration ---
# Choose a Whisper model size (e.g., 'base', 'small', 'medium', 'large')
WHISPER_MODEL_SIZE = "base"

# --- Hugging Face Llama Model Configuration ---
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
    # Handle this error in the endpoint

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
        n_ctx=8192, # context window size
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
    temp_audio_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio_file.read()
            tmp.write(content)
            temp_audio_file = tmp.name

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

        # --- Return Response ---
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
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {e}")
    finally:
        # --- Clean up temporary file ---
        if temp_audio_file and os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
            print(f"Cleaned up temporary file: {temp_audio_file}")