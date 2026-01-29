# from fastapi import APIRouter, HTTPException, Query
# from fastapi.responses import StreamingResponse
# import edge_tts
# import io
# import logging

# router = APIRouter()
# logger = logging.getLogger(__name__)

# # VOICE MAPPING (Neural Voices)
# VOICE_MAP = {
#     "en": "en-US-ChristopherNeural",   # Male, Deep, Clear
#     "hi": "hi-IN-MadhurNeural",        # Male, Natural Hindi
#     "mr": "mr-IN-ManoharNeural",       # Male, Natural Marathi
#     "bn": "bn-IN-BashkarNeural",       # Bengali
#     "gu": "gu-IN-NiranjanNeural",      # Gujarati
#     "ta": "ta-IN-ValluvarNeural",      # Tamil
#     "te": "te-IN-MohanNeural",         # Telugu
#     "kn": "kn-IN-GaganNeural",         # Kannada
#     "ml": "ml-IN-MidhunNeural",        # Malayalam
#     # Fallback
#     "default": "en-US-ChristopherNeural"
# }

# @router.get("/speak")
# async def generate_audio(text: str = Query(...), lang: str = Query("en")):
#     """
#     Generates MP3 audio using Microsoft Edge's Neural TTS.
#     Returns a streaming response of the audio file.
#     """
#     if not text:
#         raise HTTPException(status_code=400, detail="Text is required")

#     try:
#         # Select voice
#         voice = VOICE_MAP.get(lang.lower(), VOICE_MAP["default"])
#         logger.info(f"🗣️ TTS Request: '{text}' in {lang} using {voice}")

#         # Generate Audio in Memory
#         communicate = edge_tts.Communicate(text, voice)
        
#         # Create a generator to stream chunks
#         async def audio_stream():
#             async for chunk in communicate.stream():
#                 if chunk["type"] == "audio":
#                     yield chunk["data"]

#         return StreamingResponse(audio_stream(), media_type="audio/mpeg")

#     except Exception as e:
#         logger.error(f"❌ TTS Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# from services.tts_service import tts_service

# @router.get("/speak/server")
# def speak_on_server(text: str = Query(...)):
#     """
#     Triggers TTS on the SERVER (Laptop) speakers directly.
#     """
#     if not text:
#         raise HTTPException(status_code=400, detail="Text is required")
    
#     logger.info(f"🔊 Server-Side Playback Request: '{text}'")
#     try:
#         tts_service.speak(text)
#         return {"status": "playing", "message": f"Playing '{text}' on server"}
#     except Exception as e:
#         logger.error(f"❌ Server Playback Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, HTTPException, Query
import logging
from services.tts_service import tts_service

router = APIRouter()
logger = logging.getLogger(__name__)
logger.info("✅ audio.py module loaded (Pygame version)")

# VOICE MAPPING (Neural Voices)
VOICE_MAP = {
    "en": "en-US-ChristopherNeural",   # Male, Deep, Clear
    "hi": "hi-IN-MadhurNeural",        # Male, Natural Hindi
    "mr": "mr-IN-ManoharNeural",       # Male, Natural Marathi
    "bn": "bn-IN-BashkarNeural",       # Bengali
    "gu": "gu-IN-NiranjanNeural",      # Gujarati
    "ta": "ta-IN-ValluvarNeural",      # Tamil
    "te": "te-IN-MohanNeural",         # Telugu
    "kn": "kn-IN-GaganNeural",         # Kannada
    "ml": "ml-IN-MidhunNeural",        # Malayalam
    # Fallback
    "default": "en-US-ChristopherNeural"
}

@router.post("/speak/stop")
async def stop_server_audio():
    """Forcefully stops the audio playback on the laptop."""
    try:
        tts_service.stop()
        return {"status": "stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/speak/server")
async def speak_on_server(text: str = Query(...), lang: str = Query("en")):
    """Triggers TTS on the Laptop speakers using Pygame."""
    logger.info(f"🔊 Pygame TTS Request: '{text}'")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    # 1. Stop any existing audio first
    tts_service.stop()

    try:
        # Use the shared tts_service which uses Pygame and EdgeTTS
        tts_service.speak(text, lang)
        
        return {"status": "playing", "gesture": text}

    except Exception as e:
        logger.error(f"❌ Server Playback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))