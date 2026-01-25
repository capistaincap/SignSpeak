# test_pipeline.py
import time
from services.gemini_service import gemini_service
from services.tts_service import tts_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pipeline():
    print("--- 🧪 STARTING PIPELINE TEST ---")
    
    # 1. Simulate Words
    words = ["Hello", "World", "I", "Am", "Robot"]
    print(f"1. input Words: {words}")
    
    # 2. Test Gemini
    print("\n2. Testing Gemini Service...")
    try:
        sentence = gemini_service.generate_sentence(words)
        if sentence:
            print(f"✅ Gemini Success: {sentence}")
        else:
            print("❌ Gemini Failed (returned None)")
            return
    except Exception as e:
        print(f"❌ Gemini Exception: {e}")
        return

    # 3. Test TTS
    print("\n3. Testing TTS Service...")
    try:
        print(f"Speaking: '{sentence}'")
        tts_service.speak(sentence)
        print("✅ TTS Triggered (Listen for audio)")
    except Exception as e:
        print(f"❌ TTS Exception: {e}")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    test_pipeline()
