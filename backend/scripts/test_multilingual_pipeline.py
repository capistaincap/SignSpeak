
import sys
import os
import asyncio
import logging

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gemini_service import gemini_service
from services.tts_service import tts_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ManualTest")

async def main():
    print("\n✨ --- SignSpeak Interactive Test Tool --- ✨")
    print("Test Gemini Translation & TTS without the glove.")
    print("---------------------------------------------")
    
    while True:
        try:
            print("\n📝 Enter simulated gesture words (or 'q' to quit):")
            user_input = input("> ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("👋 Exiting...")
                break
                
            if not user_input:
                continue

            print("\n🌐 Enter Target Language Code (default: en):")
            print("   Options: en, hi, mr, es, fr, de, ja, zh, ar...")
            lang = input("> ").strip().lower()
            if not lang: 
                lang = 'en'
            
            print(f"\n🔄 Processing: '{user_input}' -> Gemini ({lang})...")
            
            # 1. Gemini
            words = user_input.split()
            sentence = gemini_service.generate_sentence(words, target_language=lang)
            
            if sentence:
                print(f"✅ Generated Sentence: \"{sentence}\"")
                
                # 2. TTS
                print(f"🔊 Playing Audio ({lang})...")
                # Using a temp file for playback
                tts_service.speak(sentence, lang=lang)
                
            else:
                print("❌ Gemini returned no result.")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
