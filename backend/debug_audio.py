import pyttsx3
import asyncio
import edge_tts
import pygame
import os
import time

TEMP_FILE = "debug_audio.mp3"

def test_offline():
    print("\n[1/3] Testing Offline TTS (pyttsx3)...")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say("Testing offline text to speech.")
        engine.runAndWait()
        print("✅ Offline TTS command sent.")
    except Exception as e:
        print(f"❌ Offline TTS Failed: {e}")

async def test_online():
    print("\n[2/3] Generating Online TTS (Edge)...")
    try:
        communicate = edge_tts.Communicate("Testing online text to speech.", "en-US-AriaNeural")
        await communicate.save(TEMP_FILE)
        print(f"✅ Audio file saved to {TEMP_FILE} ({os.path.getsize(TEMP_FILE)} bytes)")
        return True
    except Exception as e:
        print(f"❌ Online Generation Failed: {e}")
        return False

def test_playback():
    print("\n[3/3] Playing Audio via Pygame...")
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(TEMP_FILE)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        pygame.mixer.quit()
        print("✅ Playback finished.")
    except Exception as e:
        print(f"❌ Playback Failed: {e}")

if __name__ == "__main__":
    test_offline()
    if asyncio.run(test_online()):
        test_playback()
    
    if os.path.exists(TEMP_FILE):
        try:
            os.remove(TEMP_FILE)
        except:
            pass
