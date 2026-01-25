# test_tts.py
from services.tts_service import tts_service
import time

print("🔊 Testing TTS Service...")
print("1. Playing 'Hello' with Edge TTS...")
tts_service.speak("Hello, this is a test of the SignSpeak system.")

time.sleep(5)
print("✅ Test Complete (Did you hear it?)")
