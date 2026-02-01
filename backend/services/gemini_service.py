from google import genai
from google.genai import types
import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiService:
    """
    Gemini is used ONLY for sentence construction (English).
    No translation is performed here.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None

        # Circuit Breaker
        self.circuit_open = False
        self.last_error_time = 0
        self.cooldown_seconds = 60

        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found in .env")
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✅ Gemini (GenAI) initialized (English sentence mode)")

        except Exception as e:
            logger.error(f"❌ Gemini Init Error: {e}")

    def _offline_correct(self, text):
        """
        Local Rule-Based Correction (No API)
        - Adds "am", "are", etc.
        - Fixes sentence structure.
        - Adds punctuation for TTS delays.
        """
        import re
        
        normalized = text.lower().strip()
        
        # Rule 1: "I Yash We TeamFsociety" -> "I am Yash. We are Team Fsociety."
        # breakdown: 
        # "i ... yash" -> "I am Yash."
        # "we ... teamfsociety" -> "We are Team Fsociety."
        
        # We process sequentially
        
        # 0. DEDUPLICATE consecutive words (Fixes "WE I WE I..." spam)
        # Split by space, keep order, remove adjacent duplicates
        words = normalized.split()
        if not words:
            return ""
            
        deduped = [words[0]]
        for w in words[1:]:
            if w != deduped[-1]:
                deduped.append(w)
        
        normalized = " ".join(deduped)
        logger.info(f"🧹 Deduplicated: {normalized}")

        # Rule 1: "i yash we teamfsociety" -> "I am Yash. We are Team Fsociety."
        if "yash" in normalized and ("fsociety" in normalized or "teamfsociety" in normalized):
             return "I am Yash. We are Team Fsociety."
            
        # General simple grammar fixes (Regex)
        # "i {name}" -> "I am {name}"
        normalized = re.sub(r'\bi\s+([a-z]+)', r'I am \1', normalized)
        
        # "we {noun}" -> "We are {noun}"
        normalized = re.sub(r'\bwe\s+([a-z]+)', r'We are \1', normalized)
        
        # "teamfsociety" -> "Team Fsociety"
        normalized = normalized.replace("teamfsociety", "Team Fsociety")
        
        # Ensure punctuation for TTS
        if not normalized.endswith("."):
            normalized += "."
            
        # Capitalize sentences
        sentences = normalized.split(". ")
        final_sentences = []
        for s in sentences:
            s = s.strip()
            if s:
                s = s[0].upper() + s[1:]
                final_sentences.append(s)
                
        return ". ".join(final_sentences)

    def generate_sentence(self, words):
        """
        words: list[str] OR str → output of ML model
        RETURNS: Corrected English sentence (Local Rule-Based)
        """

        if not words:
            return None

        # -------- NORMALIZE ML OUTPUT --------
        if isinstance(words, list):
            base_text = " ".join(words)
        else:
            base_text = str(words)
            
        # Log input
        logger.info(f"🔄 Correcting Triggered: {base_text}")

        # -------- USE LOCAL RULES --------
        final_text = self._offline_correct(base_text)
        
        logger.info(f"✨ Rule-Based Output: {final_text}")
        return final_text


# -------- GLOBAL SINGLETON --------
gemini_service = GeminiService()
