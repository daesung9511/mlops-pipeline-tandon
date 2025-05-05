import os
import tempfile
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import necessary libraries for ONNX model
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForCausalLM
import onnxruntime # Required by optimum

import whisper

# --- Whisper Configuration ---
# model size (e.g., 'base', 'small', 'medium', 'large')
WHISPER_MODEL_SIZE = "base"

# --- ONNX Model Configuration ---
# This directory should contain files like decoder_model.onnx, tokenizer.json, config.json, etc.
# Use os.path.expanduser to correctly resolve the '~' to the user's home directory
ONNX_MODEL_PATH = os.path.expanduser("~/models/onnx")

# --- Initialize Models ---
# Load models globally on application startup with error handling
whisper_model = None
tokenizer = None
onnx_model = None

try:
    print(f"Loading Whisper model: {WHISPER_MODEL_SIZE}...")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    print("Whisper model loaded.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    # Handle this error in the endpoint

try:
    print(f"Loading ONNX tokenizer from {ONNX_MODEL_PATH}...")
    # AutoTokenizer will load the correct tokenizer based on the files in the directory
    tokenizer = AutoTokenizer.from_pretrained(ONNX_MODEL_PATH)
    print("ONNX tokenizer loaded.")

    print(f"Loading ONNX model from {ONNX_MODEL_PATH}...")
    # ORTModelForCausalLM is used for causal language models (like Llama) in ONNX format.
    # If provider not specified, ONNX Runtime tries to find the best available provider.
    # Explicitly setting it can be helpful for debugging or ensuring a specific device is used.
    provider="CUDAExecutionProvider" # NVIDIA GPU
    # Check if the provider is available before trying to use it
    if provider not in onnxruntime.get_available_providers():
        print(f"Warning: Provider '{provider}' not available. Falling back to default.")
        provider = None # Let ONNX Runtime choose the best available
        onnx_model = ORTModelForCausalLM.from_pretrained(ONNX_MODEL_PATH)
    else:
        onnx_model = ORTModelForCausalLM.from_pretrained(ONNX_MODEL_PATH, provider=provider)


    print("ONNX model loaded.")
except Exception as e:
    print(f"Error loading ONNX model or tokenizer from {ONNX_MODEL_PATH}: {e}")
    tokenizer = None
    onnx_model = None


# --- FastAPI App ---
app = FastAPI(
    title="Vizario: Meeting Summarization and Q&A (ONNX Llama)",
    description="API to process meeting audio using Whisper for transcription and ONNX Llama for summarization or question answering.",
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
    and then either summarizes the transcript or answers a question using an ONNX Llama model.

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
    # Check if ONNX models were loaded successfully
    if not tokenizer or not onnx_model:
         raise HTTPException(status_code=500, detail=f"ONNX model or tokenizer failed to load on startup from {ONNX_MODEL_PATH}. Check the path and model files.")


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

        # --- Process with ONNX Llama (Summarization or Q&A) ---
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
            # Tokenize the prompt
            inputs = tokenizer(prompt, return_tensors="pt") # Return PyTorch tensors

            # Generate text using the ONNX model's generate method
            # max_new_tokens specifies the maximum number of tokens to generate *after* the prompt.
            # The generate method handles the inference loop, KV cache, etc.
            # Stopping sequences might need post-processing if the generate method doesn't support them directly.
            # For Q&A, a shorter generation length is usually sufficient.
            generated_ids = onnx_model.generate(
                inputs.input_ids,
                max_new_tokens=256,
                temperature=0.1, # low for deterministic answers
                do_sample=True if 0.1 > 1e-6 else False # Enable sampling if temperature > 0
            )

            # Decode the generated text
            # The output includes the input prompt tokens, so slice them off
            generated_text = tokenizer.decode(generated_ids[0, inputs.input_ids.shape[-1]:], skip_special_tokens=True)

            # Post-process to stop at stop sequences if needed (optimum generate might not handle this natively)
            stop_sequences = ["\n", "Question:"] # Stop sequences for Q&A
            for seq in stop_sequences:
                if seq in generated_text:
                    generated_text = generated_text.split(seq, 1)[0] # Split and take the part before the first stop sequence
                    break # Stop checking once the first stop sequence is found

            result_text = generated_text.strip()

        else: # No query, perform summarization
            processing_task = "Summarization"
            print("Performing summarization.")
            prompt = f"""Summarize the following meeting transcript, highlighting key topics and decisions:

Transcript:
{transcript_text}

Summary:"""
            # Tokenize the prompt
            inputs = tokenizer(prompt, return_tensors="pt")

            # Generate text for summarization
            # A longer generation length is appropriate for summaries.
            generated_ids = onnx_model.generate(
                inputs.input_ids,
                max_new_tokens=512, # Generate up to 512 new tokens for the summary
                temperature=0.7, # Use a moderate temperature for more creative summaries
                do_sample=True if 0.7 > 1e-6 else False # Enable sampling if temperature > 0
            )

            # Decode the generated text
            generated_text = tokenizer.decode(generated_ids[0, inputs.input_ids.shape[-1]:], skip_special_tokens=True)

            # Post-process to stop at stop sequences
            stop_sequences = ["\nTranscript:"] # Stop sequences for summarization
            for seq in stop_sequences:
                if seq in generated_text:
                    generated_text = generated_text.split(seq, 1)[0]
                    break

            result_text = generated_text.strip()

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