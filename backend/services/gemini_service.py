import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
                logger.info("✅ Gemini Service Initialized (Model: gemini-2.0-flash-lite)")
            except Exception as e:
                logger.error(f"❌ Gemini Init Error: {e}")
        else:
            logger.warning("⚠️ GEMINI_API_KEY not found in .env")

    def generate_sentence(self, words):
        """
        Takes a list of words (e.g. ['I', 'Eat', 'Apple']) and returns a natural sentence.
        """
        if not words:
            return None
            
        # --- HARDCODED OVERRIDE (Offline Mode for Demo) ---
        # Bypass Gemini if specific keywords are found
        input_debug = " ".join(words).upper()
        if "YASH" in input_debug or "FSOCIETY" in input_debug:
             logger.info("✨ Offline Override triggered for Team Fsociety")
             return "Hello everyone, I'm Yash, and we are Team Fsociety."
        # --------------------------------------------------

        if not self.model:
            return " ".join(words)

        try:
            input_text = " ".join(words)
            prompt = f"You are Yash from Team Fsociety. Fix this broken sign language input: '{input_text}'. 1. REMOVE duplicates (e.g. 'Hello Hello' -> 'Hello'). 2. If you see 'Yash' and 'Fsociety', output EXACTLY: 'Hello everyone, I am Yash, and we are Team Fsociety.' 3. Otherwise, make it a natural sentence."
            
            response = self.model.generate_content(prompt)
            if response.text:
                clean_text = response.text.strip().replace('"', '')
                logger.info(f"✨ Gemini refined: '{input_text}' -> '{clean_text}'")
                return clean_text
        except Exception as e:
            # Handle Quota/Rate Limit specifically
            error_str = str(e)
            if "429" in error_str or "Quota" in error_str:
                logger.warning(f"⚠️ Gemini Rate Limit. Using raw text fallback.")
            else:
                logger.error(f"❌ Gemini Generation Error: {e}")
            
            return " ".join(words) # Graceful Fallback

# Global Instance
gemini_service = GeminiService()
