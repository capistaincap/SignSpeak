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


from fastapi import APIRouter, HTTPException, Query, Response
import edge_tts
import asyncio
import os
import signal
import subprocess
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ... (Keep your VOICE_MAP here) ...

# Global variable to track the playback process
current_playback_proc = None

@router.post("/speak/stop")
async def stop_server_audio():
    """Forcefully stops the audio playback on the laptop."""
    global current_playback_proc
    if current_playback_proc:
        try:
            # On Windows, this kills the player process
            current_playback_proc.terminate()
            # If using 'start' command, we might need a harsher kill:
            os.system("taskkill /IM mpv.exe /F /T") # or wmplayer.exe
            logger.info("🛑 Playback stopped by user toggle.")
            current_playback_proc = None
            return {"status": "stopped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "idle"}

@router.get("/speak/server")
async def speak_on_server(text: str = Query(...), lang: str = Query("en")):
    """Triggers TTS on the Laptop speakers and tracks the process."""
    global current_playback_proc
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    # 1. Stop any existing audio first
    await stop_server_audio()

    try:
        voice = VOICE_MAP.get(lang.lower(), VOICE_MAP["default"])
        output_file = "temp_speech.mp3"
        
        # 2. Generate the file using edge-tts (Command Line tool is often faster for server-side)
        # We use Popen so it doesn't block the FastAPI loop
        cmd = f'edge-tts --voice {voice} --text "{text}" --write-media {output_file} && ffplay -nodisp -autoexit {output_file}'
        
        # Note: 'ffplay' is excellent for this. If you don't have it, use 'start' or 'mpv'
        current_playback_proc = subprocess.Popen(cmd, shell=True)
        
        return {"status": "playing", "gesture": text}

    except Exception as e:
        logger.error(f"❌ Server Playback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))