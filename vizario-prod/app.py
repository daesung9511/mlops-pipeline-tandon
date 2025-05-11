import os
import tempfile
import shutil
import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import whisper
import boto3
import uuid
from transformers import BartTokenizer, BartForConditionalGeneration
import torch

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

# --- Bart Model Configuration (Local Path) ---
# Path to your locally downloaded/trained Bart model
# Default is based on the provided evaluation code
BART_MODEL_PATH = os.environ.get('BART_MODEL_PATH', '/workspace/models/facebook/bart-large')

# --- Initialize Models ---
# Load models globally on application startup with error handling
whisper_model = None
# Removed Llama variables
# llm = None
# llama_model_path_cached = None # To store the path where the model is cached

# Added Bart variables
bart_tokenizer = None
bart_model = None
bart_device = "cuda" if torch.cuda.is_available() else "cpu" # Use GPU if available

try:
    print(f"Loading Whisper model: {WHISPER_MODEL_SIZE}...")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    print("Whisper model loaded.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    # Handle this error in the endpoint (already have checks there)

# Removed Llama loading block
# try:
#     print(f"Attempting to download Llama model '{HF_FILE_NAME}' from '{HF_REPO_ID}'...")
#     # hf_hub_download caches the model, subsequent calls are fast
#     llama_model_path_cached = hf_hub_download(
#         repo_id=HF_REPO_ID,
#         filename=HF_FILE_NAME
#     )
#     print(f"Llama model downloaded/cached to: {llama_model_path_cached}")

#     print("Loading Llama model...")
#     # n_gpu_layers, n_ctx, etc. - adjust based on your model and hardware
#     llm = Llama(
#         model_path=llama_model_path_cached, # Use the cached path
#         n_gpu_layers=999, # Set > 0 if we use GPU
#         n_ctx=4096, # context window size (FIXME: MIGHT BE TOO SMALL)
#         verbose=False
#     )
#     print("Llama model loaded.")
# except Exception as e:
#     print(f"Error downloading or loading Llama model: {e}")
#     llm = None # Set to None if loading fails

# Added Bart loading block
try:
    print(f"Loading Bart model from local path: {BART_MODEL_PATH}...")
    bart_tokenizer = BartTokenizer.from_pretrained(BART_MODEL_PATH)
    bart_model = BartForConditionalGeneration.from_pretrained(BART_MODEL_PATH).to(bart_device)
    print(f"Bart model loaded to device: {bart_device}")
except Exception as e:
    print(f"Error loading Bart model from local path '{BART_MODEL_PATH}': {e}")
    bart_tokenizer = None
    bart_model = None


# --- FastAPI App ---
app = FastAPI(
    title="Vizario: Meeting Summarization and Q&A",
    description="API to process meeting audio using Whisper for transcription and Bart for summarization or question answering.",
    version="0.1.0"
)

# --- Define Response Models using Pydantic ---
class BaseMeetingResponse(BaseModel):
    interaction_id: str = Field(..., description="The unique ID for this interaction.")
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
    and then either summarizes the transcript or answers a question using Bart.
    Saves results and original audio to MinIO in the background.

    Args:
        audio_file (UploadFile): The meeting audio file (e.g., .wav, .mp3, .m4a).
        query (str, optional): A question to ask about the meeting transcript.
                                If provided, performs Q&A. If None, performs summarization.

    Returns:
        MeetingSummaryResponse | MeetingQAResponse: The response containing transcript and summary or answer.
    """
    # Check if models were loaded successfully on startup
    # Updated check for Bart model and tokenizer
    if not whisper_model:
        raise HTTPException(status_code=500, detail="Whisper model failed to load on startup.")
    if not bart_model or not bart_tokenizer:
         raise HTTPException(status_code=500, detail=f"Bart model or tokenizer failed to load from path '{BART_MODEL_PATH}' on startup.")

    # --- Save uploaded audio to a temporary file ---
    temp_audio_file = None # Declare before try block
    processing_uuid = "-1" # Default in case MinIO is not initialized
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

        # --- Process with Bart (Summarization or Q&A) ---
        result_text = ""
        processing_task = "Summarization" # Default task
        input_string = ""
        max_output_length = 0

        if query:
            processing_task = "Question Answering"
            print(f"Performing Q&A with query: '{query}' using Bart.")
            # Input format based on QMSum evaluation code
            input_string = f"question: {query} context: {transcript_text}"
            max_output_length = 200 # Limit output length for answer
        else: # No query, perform summarization
            processing_task = "Summarization"
            print("Performing summarization using Bart.")
            # Simple summarization input format
            input_string = f"Summarize the following meeting transcript: {transcript_text}"
            max_output_length = 400 # Limit output length for summary

        print(f"Bart input string (first 200 chars): {input_string[:200]}...")

        # Tokenize input string
        inputs = bart_tokenizer(
            input_string,
            return_tensors="pt",
            max_length=bart_tokenizer.model_max_length, # Use model's max length
            truncation=True
        )
        # Move input tensors to the same device as the model
        inputs = {k: v.to(bart_device) for k, v in inputs.items()}

        # Generate output using Bart model
        # Run blocking model inference in an executor
        generate_output = await loop.run_in_executor(
            None,
            lambda: bart_model.generate(
                **inputs,
                max_length=max_output_length,
                num_beams=4, # Example beam search parameter
                early_stopping=True
            )
        )

        # Decode the generated output
        result_text = bart_tokenizer.decode(generate_output[0], skip_special_tokens=True)
        print(f"Bart processing complete. Result: {result_text[:200]}...") # Print first 200 chars of result

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
                "timestamp_utc": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "bart_model_path": BART_MODEL_PATH # Add model path to metadata
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
            # processing_uuid remains "-1" if MinIO is not initialized

        # --- Return Response ---
        # The endpoint returns immediately after initiating background tasks
        if query:
            return MeetingQAResponse(
                interaction_id=processing_uuid,
                filename=audio_file.filename,
                transcript=transcript_text,
                processing_task=processing_task,
                query=query,
                answer=result_text
            )
        else:
             return MeetingSummaryResponse(
                interaction_id=processing_uuid,
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

# --- Endpoint for Receiving Feedback (NEW) ---
@app.post("/feedback/rating")
async def submit_feedback_rating(feedback: FeedbackRequest):
    """
    Receives user feedback rating for a previously processed meeting interaction.
    Updates the metadata stored in Minio for the given interaction ID.
    """
    if not s3_client:
        raise HTTPException(status_code=500, detail="MinIO client not initialized. Cannot save feedback.")

    # Construct the S3 key for the metadata file using the interaction_id
    # This assumes your metadata object key pattern is metadata/{interaction_id}/metadata.json
    metadata_object_key = f"metadata/{feedback.interaction_id}/metadata.json"
    bucket_name = MINIO_BUCKET_NAME # Get bucket name from config

    print(f"Received feedback for interaction ID: {feedback.interaction_id}")
    print(f"Helpful: {feedback.helpful}, Feedback Text: {feedback.feedback_text}")

    loop = asyncio.get_event_loop() # Get the current event loop

    try:
        # 1. Retrieve the existing metadata object from MinIO
        print(f"Attempting to retrieve metadata from MinIO: {metadata_object_key}")
        response = await loop.run_in_executor(
            None,
            lambda: s3_client.get_object(Bucket=bucket_name, Key=metadata_object_key)
        )
        existing_metadata_bytes = await loop.run_in_executor(None, lambda: response['Body'].read())
        existing_metadata = json.loads(existing_metadata_bytes.decode('utf-8'))
        print("Metadata retrieved successfully.")

        # 2. Update the metadata with the new feedback
        existing_metadata["user_rating_helpful"] = feedback.helpful
        existing_metadata["user_feedback_text"] = feedback.feedback_text
        existing_metadata["feedback_timestamp_utc"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') # Add timestamp for feedback

        # 3. Save the updated metadata back to Minio (overwrite the old object)
        updated_metadata_bytes = json.dumps(existing_metadata, indent=2).encode('utf-8')
        print(f"Attempting to save updated metadata to MinIO: {metadata_object_key}")
        await loop.run_in_executor(
            None,
            lambda: s3_client.put_object(
                Bucket=bucket_name,
                Key=metadata_object_key,
                Body=updated_metadata_bytes,
                ContentType='application/json'
            )
        )
        print("Updated metadata saved successfully.")

        return {"message": f"Feedback received and saved for interaction ID: {feedback.interaction_id}"}

    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"Error: Metadata object not found for interaction ID: {feedback.interaction_id}")
            raise HTTPException(status_code=404, detail=f"Interaction with ID {feedback.interaction_id} not found.")
        else:
            print(f"An S3 error occurred while processing feedback: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred while saving feedback: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while processing feedback: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing feedback: {e}")