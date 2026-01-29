import pyttsx3
import threading
import logging
import asyncio
import edge_tts
import os
import tempfile
import uuid
import pygame

logger = logging.getLogger(__name__)


# =========================================================
# OFFLINE TRANSLATION MAP (FIXED SENTENCE TRANSLATION)
# =========================================================
OFFLINE_SENTENCE_TRANSLATIONS = {
    "hi": {
        "hello, i am yash. we are team fsociety.": "नमस्ते, मैं यश हूँ। हम टीम एफसोसाइटी हैं।",
    },
    "mr": {
        "hello, i am yash. we are team fsociety.": "नमस्कार, मी यश आहे. आम्ही टीम एफसोसायटी आहोत.",
    },
    "ta": {
        "hello, i am yash. we are team fsociety.": "வணக்கம், நான் யாஷ். நாங்கள் டீம் எஃப்சொசைட்டி.",
    },
    "bn": {
        "hello, i am yash. we are team fsociety.": "নমস্কার, আমি যশ। আমরা টিম এফসোসাইটি।",
    }
}


class TTSService:
    def __init__(self):
        self.lock = threading.Lock()

        # ---------- Init pygame ----------
        try:
            pygame.mixer.init()
            logger.info("✅ Pygame mixer initialized")
        except Exception as e:
            logger.error(f"❌ Pygame Init Error: {e}")

        # ---------- Offline fallback ----------
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)
            logger.info("✅ pyttsx3 fallback initialized")
        except Exception as e:
            self.engine = None
            logger.error(f"❌ pyttsx3 Init Error: {e}")

        logger.info("🎧 TTS Service Ready (Edge + Offline Translation)")

        # ---------- VOICE MAP ----------
        self.voices = {
            "en": "en-US-AriaNeural",
            "hi": "hi-IN-SwaraNeural",
            "mr": "mr-IN-AarohiNeural",
            "bn": "bn-IN-TanishaaNeural",
            "gu": "gu-IN-DhwaniNeural",
            "ta": "ta-IN-PallaviNeural",
            "te": "te-IN-ShrutiNeural",
            "kn": "kn-IN-SapnaNeural",
            "ml": "ml-IN-SobhanaNeural",
            "ur": "ur-IN-GulNeural",
        }

    # =====================================================
    # PUBLIC API
    # =====================================================
    def speak(self, text, lang="en", play=True, output_file=None):
        if not text:
            return None

        lang = str(lang).lower().strip()

        thread = threading.Thread(
            target=self._speak_worker,
            args=(text, lang, play, output_file),
            daemon=True
        )
        thread.start()

    # =====================================================
    # WORKER
    # =====================================================
    def _speak_worker(self, text, lang, play, output_file):
        with self.lock:
            try:
                asyncio.new_event_loop().run_until_complete(
                    self._speak_edge(text, lang, play, output_file)
                )
            except Exception as e:
                logger.error(f"❌ Edge TTS failed: {e}")
                self._speak_fallback(text)

    # =====================================================
    # EDGE TTS (WITH OFFLINE TRANSLATION)
    # =====================================================
    async def _speak_edge(self, text, lang, play, output_file):

        # ---------- TRANSLATE FIXED SENTENCE ----------
        original_text = text.strip().lower()
        if lang != "en":
            translated = OFFLINE_SENTENCE_TRANSLATIONS.get(lang, {}).get(original_text)
            if translated:
                logger.info(f"🌍 Offline translation applied ({lang})")
                text = translated
            else:
                logger.warning(f"⚠️ No offline translation found for lang={lang}, speaking English")

        # ---------- VOICE CHECK ----------
        if lang not in self.voices:
            raise ValueError(f"No TTS voice for language: {lang}")

        voice = self.voices[lang]

        if not output_file:
            filename = f"signspeak_{uuid.uuid4().hex}.mp3"
            output_file = os.path.join(tempfile.gettempdir(), filename)

        logger.info(f"🗣️ TTS | LANG={lang} | VOICE={voice} | TEXT={text}")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)

        if play:
            self._play_audio(output_file)

        return output_file

    # =====================================================
    # PLAYBACK
    # =====================================================
    def _play_audio(self, file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"❌ Playback Error: {e}")

    # =====================================================
    # FALLBACK (ENGLISH)
    # =====================================================
    def _speak_fallback(self, text):
        if not self.engine:
            return
        try:
            logger.warning("🗣️ Using offline pyttsx3 fallback")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"❌ Fallback Error: {e}")

    # =====================================================
    # STOP
    # =====================================================
    def stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass


# -------- GLOBAL INSTANCE --------
tts_service = TTSService()
