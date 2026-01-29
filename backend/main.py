from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import audio, sensors

from services.udp_service import udp_service
# from services.polling_service import polling_service
from services.serial_service import serial_service
from services.ml_service import ml_service
from services.tts_service import tts_service
from services.gemini_service import gemini_service
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
word_buffer = []
last_detection_time = 0.0
last_spoken_time = 0.0
last_gemini_request_time = 0.0

SILENCE_THRESHOLD = 3.0        # seconds (pause before sentence formation)
GEMINI_MIN_INTERVAL = 10.0     # seconds (quota protection)

buffer_lock = threading.Lock()

# ---------------- CALLBACKS ----------------
def on_ml_prediction(word: str):
    """
    Called when ML detects a stable gesture
    """
    global last_detection_time, last_spoken_time

    logger.info(f"📥 ML stable word: {word}")

    # Update frontend with raw gesture
    data_store.update({"gesture": word})

    # Buffer words safely
    with buffer_lock:
        if not word_buffer or word_buffer[-1] != word:
            word_buffer.append(word)

    last_detection_time = time.time()

    # -------- AI OFF MODE (DEBUG / DEMO) --------
    use_gemini = data_store.config.get("use_gemini", True)
    auto_speak = data_store.config.get("auto_speak", False)
    target_lang = data_store.config.get("lang", "en")

    if not use_gemini and auto_speak:
        if time.time() - last_spoken_time > 1.5:
            tts_service.speak(word, lang=target_lang)
            last_spoken_time = time.time()


def on_serial_data(flex, acc):
    """
    Called when Serial / UDP receives new sensor data
    """
    ml_service.process_data(flex, acc)

# ---------------- BACKGROUND TASK ----------------
async def sentence_formation_loop():
    """
    Forms sentences after silence using Gemini (English only)
    """
    global last_gemini_request_time, last_spoken_time

    logger.info("⏳ Sentence formation loop started")

    loop = asyncio.get_event_loop()

    try:
        while True:
            await asyncio.sleep(0.5)

            # Wait until silence window is crossed
            if time.time() - last_detection_time <= SILENCE_THRESHOLD:
                continue

            # Safely extract buffered words
            with buffer_lock:
                if not word_buffer:
                    continue
                raw_words = word_buffer.copy()
                word_buffer.clear()

            # Throttle Gemini calls (quota safety)
            if time.time() - last_gemini_request_time < GEMINI_MIN_INTERVAL:
                logger.info("⏸️ Gemini throttled, skipping cycle")
                continue

            logger.info(f"📝 Forming sentence from: {raw_words}")
            data_store.update({"sentence": "Processing..."})

            use_gemini = data_store.config.get("use_gemini", True)
            auto_speak = data_store.config.get("auto_speak", False)
            target_lang = data_store.config.get("lang", "en")

            # -------- SENTENCE GENERATION (GEMINI DISABLED) --------
            # if use_gemini:
            #     last_gemini_request_time = time.time()
            #     natural_sentence = await loop.run_in_executor(
            #         None,
            #         gemini_service.generate_sentence,
            #         raw_words
            #     )
            # else:
            #     natural_sentence = " ".join(raw_words)
            
            # FORCE RAW MODE
            natural_sentence = " ".join(raw_words)

            if not natural_sentence:
                continue

            # Update frontend with final sentence (ENGLISH)
            data_store.update({"sentence": natural_sentence})

            # Speak sentence in selected language
            if auto_speak:
                tts_service.speak(natural_sentence, lang=target_lang)
                last_spoken_time = time.time()

    except asyncio.CancelledError:
        logger.info("🛑 Sentence formation loop cancelled")
        raise
    except Exception as e:
        logger.error(f"❌ Error in sentence loop: {e}")

# ---------------- STARTUP / SHUTDOWN ----------------
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting SignSpeak Backend")

    try:
        ml_service.register_callback(on_ml_prediction)
        serial_service.register_callback(on_serial_data)
        udp_service.register_callback(on_serial_data)
        # polling_service.register_callback(on_serial_data)

        udp_service.start()
        # polling_service.start()
        serial_service.start()

        asyncio.create_task(sentence_formation_loop())

        logger.info("🧠 Mode: Gemini (Sentence) + Offline TTS Translation")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down backend")
    udp_service.stop()
    # polling_service.stop()
    # serial_service.stop()  # optional

# ---------------- ROUTES ----------------
app.include_router(sensors.router)
app.include_router(audio.router, prefix="/audio", tags=["Audio"])

@app.get("/")
def root():
    return {"status": "SignSpeak backend running (WiFi / UDP mode)"}
