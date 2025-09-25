from pydantic import BaseModel
from components.models import CaseRecord
from components.gui import gui

from components.spamfilteringactual import HelplineProcessor
from components.simitestllm import subredditting
from components.scoring import scoring
from datetime import datetime

from typing import Union

from fastapi import FastAPI, Body

from db.supabase import create_supabase_client

from socketio import AsyncServer, ASGIApp
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import io
import os
import logging
import asyncio
import json
from pydub import AudioSegment
import subprocess
import uvicorn
import sys
import queue
import threading

# This policy fix MUST be at the absolute top of the script.
if sys.platform == "win32":
    # Force selector event loop policy which is more stable
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
client_states = {}

# IMPROVEMENT: Load configuration from environment variables
MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")
# MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-in-0.4")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "C:\\ffmpeg\\bin\\ffmpeg.exe")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Vosk model not found at '{MODEL_PATH}'.")

# --- Global Objects ---
VOSK_MODEL = Model(MODEL_PATH)
SAMPLE_RATE = 16000
supabase = create_supabase_client()
processor = HelplineProcessor()

# --- FastAPI and Socket.IO Setup ---
sio = AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = ASGIApp(sio)
app.mount("/", socket_app)

# --- WebSocket Audio Processing ---


class FFmpegManager:
    def __init__(self, ffmpeg_path, sample_rate):
        self.ffmpeg_path = ffmpeg_path
        self.sample_rate = sample_rate
        self.processes = {}
        self.audio_queues = {}
        self.output_queues = {}
        self.stop_events = {}

    def create_process_for_client(self, sid):
        """Create FFmpeg process and associated threads for a client"""
        try:
            # Create the subprocess using regular Popen
            process = subprocess.Popen(
                [
                    self.ffmpeg_path,
                    "-i",
                    "pipe:0",
                    "-ar",
                    str(self.sample_rate),
                    "-ac",
                    "1",
                    "-f",
                    "s16le",
                    "pipe:1",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # Unbuffered
            )

            # Create queues and events
            audio_queue = queue.Queue()
            output_queue = queue.Queue()
            stop_event = threading.Event()

            # Store references
            self.processes[sid] = process
            self.audio_queues[sid] = audio_queue
            self.output_queues[sid] = output_queue
            self.stop_events[sid] = stop_event

            # Start worker threads
            input_thread = threading.Thread(
                target=self._audio_input_worker,
                args=(sid, process, audio_queue, stop_event),
                daemon=True,
            )
            output_thread = threading.Thread(
                target=self._audio_output_worker,
                args=(sid, process, output_queue, stop_event),
                daemon=True,
            )

            input_thread.start()
            output_thread.start()

            logging.info(f"Created FFmpeg process and threads for {sid}")
            return True

        except Exception as e:
            logging.error(f"Failed to create FFmpeg process for {sid}: {e}")
            return False

    def _audio_input_worker(self, sid, process, audio_queue, stop_event):
        """Worker thread to handle audio input to FFmpeg"""
        try:
            while not stop_event.is_set() and process.poll() is None:
                try:
                    audio_data = audio_queue.get(timeout=0.1)
                    if audio_data is None:  # Sentinel to stop
                        break
                    process.stdin.write(audio_data)
                    process.stdin.flush()
                except queue.Empty:
                    continue
                except Exception as e:
                    logging.error(f"Error in audio input worker for {sid}: {e}")
                    break
        except Exception as e:
            logging.error(f"Audio input worker error for {sid}: {e}")
        finally:
            try:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            except:
                pass

    def _audio_output_worker(self, sid, process, output_queue, stop_event):
        """Worker thread to handle audio output from FFmpeg"""
        try:
            while not stop_event.is_set() and process.poll() is None:
                try:
                    raw_audio = process.stdout.read(4096)
                    if not raw_audio:
                        break
                    output_queue.put(raw_audio)
                except Exception as e:
                    logging.error(f"Error in audio output worker for {sid}: {e}")
                    break
        except Exception as e:
            logging.error(f"Audio output worker error for {sid}: {e}")
        finally:
            output_queue.put(None)  # Sentinel to indicate end

    def send_audio(self, sid, audio_data):
        """Send audio data to FFmpeg process"""
        if sid in self.audio_queues:
            try:
                self.audio_queues[sid].put_nowait(audio_data)
            except queue.Full:
                logging.warning(f"Audio queue full for {sid}, dropping audio data")

    def get_processed_audio(self, sid):
        """Get processed audio from FFmpeg (non-blocking)"""
        if sid in self.output_queues:
            try:
                return self.output_queues[sid].get_nowait()
            except queue.Empty:
                return None
        return None

    def cleanup_client(self, sid):
        """Clean up resources for a client"""
        if sid in self.stop_events:
            self.stop_events[sid].set()

        if sid in self.audio_queues:
            self.audio_queues[sid].put(None)  # Sentinel to stop input worker

        if sid in self.processes:
            process = self.processes[sid]
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

        # Clean up references
        for container in [
            self.processes,
            self.audio_queues,
            self.output_queues,
            self.stop_events,
        ]:
            container.pop(sid, None)

        logging.info(f"Cleaned up FFmpeg resources for {sid}")


# Create global FFmpeg manager
ffmpeg_manager = FFmpegManager(FFMPEG_PATH, SAMPLE_RATE)


@sio.event
async def connect(sid, environ):
    logging.info(f"Client connected: {sid}")
    print(f"🔌 NEW CONNECTION: {sid}")

    # Create FFmpeg process in thread pool
    success = await asyncio.to_thread(ffmpeg_manager.create_process_for_client, sid)

    if not success:
        print(f"❌ FFmpeg initialization failed for {sid}")
        await sio.emit(
            "error", {"message": "Failed to initialize audio processing"}, room=sid
        )
        return

    # Create recognizer
    recognizer = KaldiRecognizer(VOSK_MODEL, SAMPLE_RATE)
    client_states[sid] = {
        "recognizer": recognizer,
        "last_transcript": "",
    }

    print(f"✅ Audio processing initialized for {sid}")

    # Start audio processing task
    asyncio.create_task(process_audio_output(sid))
    logging.info(f"Started audio processing for {sid}")


async def process_audio_output(sid):
    """Process audio output from FFmpeg and handle transcription"""
    if sid not in client_states:
        return

    print(f"🎤 Starting audio processing loop for {sid}")
    recognizer = client_states[sid]["recognizer"]
    audio_chunks_received = 0

    while sid in client_states:
        try:
            # Get processed audio from FFmpeg (non-blocking)
            raw_audio = await asyncio.to_thread(ffmpeg_manager.get_processed_audio, sid)

            if raw_audio is None:
                await asyncio.sleep(0.01)  # Small delay to prevent tight loop
                continue

            if raw_audio == b"":  # End of stream
                print(f"📤 End of audio stream for {sid}")
                break

            audio_chunks_received += 1
            if audio_chunks_received % 100 == 0:  # Log every 100 chunks
                print(f"🔊 Processed {audio_chunks_received} audio chunks for {sid}")

            # Process with Vosk
            if recognizer.AcceptWaveform(raw_audio):
                result = json.loads(recognizer.Result())
                if result.get("text"):
                    final_text = result["text"]
                    print(f"[FINAL] {sid}: {final_text}")  # Print final transcription
                    logging.info(f"Final transcription for {sid}: {final_text}")
                    await sio.emit(
                        "transcription",
                        {"data": final_text, "final": True},
                        room=sid,
                    )
                    client_states[sid]["last_transcript"] = ""

            partial_result = json.loads(recognizer.PartialResult())
            partial_transcript = partial_result.get("partial", "")
            if partial_transcript and partial_transcript != client_states[sid].get(
                "last_transcript"
            ):
                print(
                    f"[PARTIAL] {sid}: {partial_transcript}"
                )  # Print partial transcription
                await sio.emit(
                    "transcription",
                    {"data": partial_transcript, "final": False},
                    room=sid,
                )
                client_states[sid]["last_transcript"] = partial_transcript

        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Error processing audio output for {sid}: {e}")
            print(f"❌ Audio processing error for {sid}: {e}")
            break

    print(
        f"🛑 Audio processing task finished for {sid} (processed {audio_chunks_received} chunks)"
    )
    logging.info(f"Audio processing task for {sid} finished.")


@sio.on("audio")
async def handle_audio(sid, audio_data):
    if sid in client_states:
        print(f"🎵 Received audio data for {sid}: {len(audio_data)} bytes")
        await asyncio.to_thread(ffmpeg_manager.send_audio, sid, audio_data)
    else:
        print(f"⚠️ Received audio for unknown client: {sid}")


@sio.event
async def disconnect(sid):
    logging.info(f"Client disconnected: {sid}")

    # Clean up client state
    if sid in client_states:
        del client_states[sid]

    # Clean up FFmpeg resources
    await asyncio.to_thread(ffmpeg_manager.cleanup_client, sid)
    logging.info(f"Cleaned up resources for {sid}")


# --- REST API Endpoints ---


class ComplaintRequest(BaseModel):
    details: str
    location: str
    caller: str
    phone: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/v1/new-complaint")
async def new_complaint(complaint: ComplaintRequest = Body(...)):
    current_datetime = datetime.now()
    grievance = CaseRecord(
        # ... (your grievance object creation)
    )

    # CRITICAL FIX: Run blocking code in a thread to avoid freezing the server
    def process_and_submit():
        logging.info("Starting background processing for new complaint.")
        result = processor.process_grievance_object(grievance)
        if result:
            subredditting(result)
            scoring()
        logging.info("Background processing finished.")
        return result

    result = await asyncio.to_thread(process_and_submit)

    return {
        "status": "Complaint received and is being processed.",
        "data": complaint.dict(),
    }


@app.get("/complaints")
async def get_complaints():
    """Fetch all complaints from the database."""

    # CRITICAL FIX: Run the blocking database call in a separate thread
    def fetch_data():
        return supabase.table("Complaint").select("*").execute()

    response = await asyncio.to_thread(fetch_data)
    return response.data if response and hasattr(response, "data") else []


# --- Server Execution ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
