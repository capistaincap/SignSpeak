"""
Final standalone test for SignSpeak pipeline

Flow:
Expected ML Output
→ Gemini sentence generation
→ TTS audio output

Run:
python -m scripts.test_gemini_tts
"""

from services.gemini_service import gemini_service
from services.tts_service import tts_service
import time


def test_pipeline():
    print("\n==============================")
    print("🔬 SignSpeak FINAL PIPELINE TEST")
    print("==============================\n")

    # ---------------- EXPECTED ML OUTPUT ----------------
    expected_ml_output = [
        "HELLO", "I", "AM", "YASH", "WE", "ARE", "TEAM", "FSOCIETY"
    ]
    target_language = "hi"   # change to en / mr / ta / bn if needed

    print(f"🧠 Expected ML Output: {expected_ml_output}")
    print(f"🌍 Target Language: {target_language}")

    # ---------------- GEMINI ----------------
    print("\n🤖 Sending to Gemini...")
    sentence = gemini_service.generate_sentence(
        expected_ml_output,
        target_language
    )

    print(f"🔥 Gemini Output: {sentence}")

    if not sentence:
        print("❌ Gemini failed to generate sentence")
        return

    # ---------------- TTS ----------------
    print("\n🔊 Speaking sentence...")
    tts_service.speak(
        sentence,
        lang=target_language,
        play=True
    )

    print("⏳ Waiting for audio to finish...")
    time.sleep(7)

    print("\n✅ FINAL TEST COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    test_pipeline()
