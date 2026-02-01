from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import audio, sensors

from services.udp_service import udp_service
from services.serial_service import serial_service
from services.ml_service import ml_service
from services.tts_service import tts_service
from services.data_store import data_store

import logging
import asyncio
import time
import threading

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- APP ----------------
app = FastAPI(title="SignSpeak Backend")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- STATE ----------------
last_detection_time = 0.0
last_spoken_time = 0.0
last_spoken_sentence = None

state_lock = threading.Lock()

# ---------------- CALLBACK ----------------
def on_ml_prediction(prediction_data):
    """
    Handles DEMO SEQUENTIAL predictions from MLService
    """
    global last_detection_time, last_spoken_time, last_spoken_sentence

    # We ONLY expect dict data in demo mode
    if not isinstance(prediction_data, dict):
        return

    word = prediction_data.get("word", "")
    sentence = prediction_data.get("sentence", "")
    confidence = prediction_data.get("confidence", 94)
    is_final = prediction_data.get("final", False)

    logger.info(f"📥 DEMO WORD RECEIVED → {word}")

    # ---------------- FRONTEND UPDATE ----------------
    data_store.update({
        "gesture": word,
        "sentence": sentence,
        "confidence": confidence,
        "stable": True
    })

    last_detection_time = time.time()

    # ---------------- AUDIO OUTPUT ----------------
    use_audio = data_store.config.get("audio", True)
    target_lang = data_store.config.get("lang", "en")

    if not use_audio:
        return

    # Speak ONLY the final AI sentence
    if is_final:
        with state_lock:
            if sentence != last_spoken_sentence:
                logger.info("🗣️ Speaking FINAL AI sentence")
                tts_service.speak(sentence, lang=target_lang)
                last_spoken_sentence = sentence
                last_spoken_time = time.time()


def on_serial_data(flex, acc):
    """
    Called whenever Serial / UDP sends sensor data
    """
    ml_service.process_data(flex, acc)

# ---------------- BACKGROUND TASK ----------------
async def keep_alive_loop():
    """
    Dummy loop to keep FastAPI async tasks alive
    """
    logger.info("⏳ Background keep-alive loop running (Demo Mode)")
    while True:
        await asyncio.sleep(60)

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting SignSpeak Backend (DEMO SEQUENTIAL MODE)")

    try:
        # Register callbacks
        ml_service.register_callback(on_ml_prediction)
        serial_service.register_callback(on_serial_data)
        udp_service.register_callback(on_serial_data)

        # Start services
        udp_service.start()
        serial_service.start()

        # Background task
        asyncio.create_task(keep_alive_loop())

        logger.info("🧠 Mode: Sequential Gesture → AI Sentence")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

# ---------------- SHUTDOWN ----------------
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down SignSpeak backend")
    udp_service.stop()
    serial_service.stop()

# ---------------- ROUTES ----------------
app.include_router(sensors.router)
app.include_router(audio.router, prefix="/audio", tags=["Audio"])

@app.get("/")
def root():
    return {
        "status": "SignSpeak backend running",
        "mode": "DEMO SEQUENTIAL + AI SENTENCE"
    }
