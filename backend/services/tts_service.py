import pyttsx3
import threading
import logging
import asyncio
import edge_tts
import os
import tempfile
import pygame

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.engine = None
        self.lock = threading.Lock()
        self.loop = None
        
        # Initialize Pygame Mixer for Audio Playback
        try:
            pygame.mixer.init()
        except Exception as e:
            logger.error(f"Pygame Init Error: {e}")

        # Initialize Fallback Engine
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            logger.info("✅ TTS Service Initialized (Edge + Fallback)")
        except Exception as e:
            logger.error(f"❌ TTS Fallback Init Error: {e}")

    def speak(self, text):
        # Run in a separate thread to avoid blocking
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        with self.lock:
            try:
                # 1. Try Edge TTS (High Quality)
                asyncio.run(self._speak_edge(text))
            except Exception as e:
                # Ignore shutdown errors
                if "atexit" in str(e) or "shutdown" in str(e):
                    return

                logger.warning(f"⚠️ Edge TTS Failed ({e}), switching to fallback...")
                # 2. Fallback to Offline TTS
                self._speak_fallback(text)

    async def _speak_edge(self, text):
        # Voice: en-US-AriaNeural or en-US-GuyNeural
        voice = "en-US-AriaNeural"
        temp_file = os.path.join(tempfile.gettempdir(), "sign_speak_temp.mp3")
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_file)
        
        # Play with Pygame
        try:
             # Re-init mixer to ensure fresh handle
            pygame.mixer.quit()
            pygame.mixer.init()
            
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            logger.error(f"Pygame Playback Error: {e}")
            raise e
            
        # Cleanup
        try:
            pygame.mixer.music.unload()
            # os.remove(temp_file) # Optional: Keep for debugging or delete
        except:
            pass

    def _speak_fallback(self, text):
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS Fallback Error: {e}")

# Global instance
tts_service = TTSService()
