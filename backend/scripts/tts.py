"""
FINAL PROOF TEST
No Gemini
No backend
No ML

If this speaks Hindi → system is correct
"""

from services.tts_service import tts_service
import time

def final_proof():
    print("\n==============================")
    print("🔊 FINAL TTS LANGUAGE PROOF")
    print("==============================\n")

    hindi_sentence = "नमस्ते, मैं यश हूँ। हम टीम एफसोसाइटी हैं।"
    lang = "hi"

    print("Text:", hindi_sentence)
    print("Lang:", lang)

    tts_service.speak(hindi_sentence, lang=lang, play=True)

    time.sleep(6)
    print("\n✅ PROOF COMPLETE")

if __name__ == "__main__":
    final_proof()
