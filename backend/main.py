from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import audio, sensors
from services.udp_service import udp_service
from services.serial_service import serial_service
from services.ml_service import ml_service
from services.tts_service import tts_service
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SignSpeak Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from services.data_store import data_store

from services.gemini_service import gemini_service
import asyncio
import time

# --- STATE ---
word_buffer = []
last_detection_time = 0
last_spoken_time = 0 # For AI-Off mode cooldown
SILENCE_THRESHOLD = 3.0 # Seconds

# --- CALLBACKS ---
def on_ml_prediction(word):
    """Callback when ML logic detects a new stable gesture"""
    global last_detection_time, last_spoken_time
    logger.info(f"Main received stable word: {word}")
    
    # Update store for frontend (raw gesture)
    data_store.update({"gesture": word})
    
    # Buffer logic
    # Dedup: Only add if distinct from last word
    if not word_buffer or word_buffer[-1] != word:
        word_buffer.append(word)
    
    last_detection_time = time.time()
    
    # AI OFF MODE: Speak Immediately (with Delay)
    use_gemini = data_store.config.get("use_gemini", True)
    auto_speak = data_store.config.get("auto_speak", False)

    if not use_gemini and auto_speak:
        # Check cooldown to avoid repetition spam
        if time.time() - last_spoken_time > 2.0:
            tts_service.speak(word)
            last_spoken_time = time.time() 

def on_serial_data(flex, acc):
    """Callback when Serial gets new sensor data"""
    ml_service.process_data(flex, acc)

# --- BACKGROUND TASK ---
async def sentence_formation_loop():
    global word_buffer
    logger.info("⏳ Sentence Formation Loop Started")
    
    while True:
        await asyncio.sleep(1) # Check every second
        
        if word_buffer and (time.time() - last_detection_time > SILENCE_THRESHOLD):
            # Form sentence
            raw_words = word_buffer.copy()
            word_buffer.clear() # Reset immediately
            
            logger.info(f"📝 Forming sentence from: {raw_words}")
            
            # Notify frontend of processing
            data_store.update({"sentence": "Processing..."})
            
            # Check Toggle (AI Enhance)
            use_gemini = data_store.config.get("use_gemini", True)
            auto_speak = data_store.config.get("auto_speak", False)
            
            natural_sentence = ""
            if use_gemini:
                natural_sentence = gemini_service.generate_sentence(raw_words)
            else:
                # Raw Mode: Just join words
                natural_sentence = " ".join(raw_words)
            
            if natural_sentence:
                # Update frontend with FULL sentence
                data_store.update({"sentence": natural_sentence})
                
                # Speak natural sentence (ONLY IF AUTO-SPEAK IS ON)
                if auto_speak:
                    tts_service.speak(natural_sentence)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up SignSpeak Backend...")
    try:
        # Wire up the system
        ml_service.register_callback(on_ml_prediction)
        serial_service.register_callback(on_serial_data)
        udp_service.register_callback(on_serial_data) # Reuse same callback for UDP
        
        udp_service.start()
        serial_service.start()
        
        # Start background loop
        asyncio.create_task(sentence_formation_loop())
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    udp_service.stop()
    # serial_service.stop()

# Routes
app.include_router(sensors.router)
app.include_router(audio.router, prefix="/audio", tags=["Audio"])

@app.get("/")
def root():
    return {"status": "SignSpeak backend running (WiFi/UDP Mode)"}
