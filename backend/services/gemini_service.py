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

    def generate_sentence(self, words):
        """
        words: list[str] OR str → output of ML model
        RETURNS: English sentence only
        """

        if not words:
            return None

        # -------- NORMALIZE ML OUTPUT --------
        if isinstance(words, list):
            base_text = " ".join(words)
        else:
            base_text = str(words)

        base_text = base_text.lower().capitalize()
        normalized = base_text.lower()
        # ------------------------------------

        # -------- DEMO OVERRIDE (SAFE & INTENTIONAL) --------
        if "yash" in normalized and "fsociety" in normalized:
            return "Hello, I am Yash. We are Team Fsociety."
        # ---------------------------------------------------

        # -------- FALLBACK IF GEMINI UNAVAILABLE --------
        if not self.client:
            return base_text
        # -----------------------------------------------

        # -------- CIRCUIT BREAKER --------
        if self.circuit_open:
            elapsed = time.time() - self.last_error_time
            if elapsed < self.cooldown_seconds:
                logger.warning("⚠️ Gemini in cooldown, using fallback sentence")
                return base_text
            self.circuit_open = False
            logger.info("♻️ Gemini recovered after cooldown")
        # --------------------------------

        # -------- ENGLISH-ONLY PROMPT --------
        prompt = f"""
        You are a sign language sentence normalizer.

        Input words:
        {base_text}

        Rules:
        - Convert the input into a clear, grammatically correct English sentence.
        - Keep names exactly as they are (example: Yash, Fsociety).
        - Do NOT translate.
        - Do NOT add new meaning.
        - Output ONLY the final sentence.
        - No explanations.

        Output:
        """
        # -----------------------------------

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.9,
                    max_output_tokens=80
                )
            )

            if response and response.text:
                final_text = response.text.strip()

                # Remove wrapping quotes if present
                if final_text.startswith('"') and final_text.endswith('"'):
                    final_text = final_text[1:-1]

                logger.info(f"✨ Gemini [EN]: {final_text}")
                return final_text

        except Exception as e:
            error = str(e).lower()

            if "429" in error or "quota" in error:
                logger.warning("⚠️ Gemini quota exceeded — circuit open (60s)")
                self.circuit_open = True
                self.last_error_time = time.time()
                return base_text

            logger.error(f"❌ Gemini Error: {e}")

        return base_text


# -------- GLOBAL SINGLETON --------
gemini_service = GeminiService()
