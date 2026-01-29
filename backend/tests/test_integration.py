
import sys
import os
import asyncio
import logging

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gemini_service import gemini_service
from services.tts_service import tts_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gemini():
    logger.info("--- Testing Gemini Service ---")
    words = ["Hello", "World", "Test"]
    logger.info(f"Input Words: {words}")
    try:
        sentence = await gemini_service.generate_sentence(words)
        logger.info(f"Generated Sentence: {sentence}")
        if sentence:
            logger.info("✅ Gemini Service Verified")
            return sentence
        else:
            logger.error("❌ Gemini Service Failed (Empty Response)")
            return None
    except Exception as e:
        logger.error(f"❌ Gemini Service Error: {e}")
        return None

async def test_tts(text):
    logger.info("--- Testing TTS Service ---")
    if not text:
        logger.warning("Skipping TTS test (No text provided)")
        return

    output_file = "test_audio_integration.mp3"
    logger.info(f"Speaking: '{text}' -> {output_file}")
    
    try:
        await tts_service.speak(text, output_file=output_file)
        
        if os.path.exists(output_file):
             # Cleanup
            file_size = os.path.getsize(output_file)
            logger.info(f"✅ TTS Audio Generated ({file_size} bytes)")
            # os.remove(output_file) # Optional: Keep to verify manually
            # logger.info("Audio file cleaned up")
        else:
            logger.error("❌ TTS Failed (File not created)")

    except Exception as e:
        logger.error(f"❌ TTS Error: {e}")

async def main():
    logger.info("🚀 Starting Multilingual Integration Test")
    
    # List of languages to test
    languages = [
        'en', 'hi', 'mr', 'es', 'fr', 'de', 'ja', 'ko', 'zh', 'ar'
        # 'bn', 'gu', 'ta', 'te' # Optional: Add back if needed (might be slower)
    ]
    
    input_words = ["Hello", "Friend", "Welcome"]
    
    results = {}
    
    for lang in languages:
        logger.info(f"\n🌐 --- Testing Language: {lang.upper()} ---")
        
        # 1. Test Gemini Translation (Synchronous)
        sentence = gemini_service.generate_sentence(input_words, target_language=lang)
        
        if not sentence:
            logger.error(f"❌ Gemini Failed for {lang}")
            results[lang] = "Gemini Failed"
            continue
            
        logger.info(f"📝 Translated: {sentence}")
        
        # 2. Test TTS Generation (Synchronous, threaded)
        output_file = f"backend/tests/test_audio_{lang}.mp3"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Remove if exists
        if os.path.exists(output_file):
            os.remove(output_file)
            
        tts_service.speak(sentence, lang=lang, output_file=output_file)
        
        # Wait for file to be created (async race condition possible with threads)
        await asyncio.sleep(3) # Increased wait time slightly
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info(f"✅ Audio Created: {output_file}")
            results[lang] = "PASS"
            # Cleanup
            # os.remove(output_file) # Keep for manual review if needed, or uncomment to clean
            os.remove(output_file)
        else:
            logger.error(f"❌ Audio Failed for {lang}")
            results[lang] = "TTS Failed"
            
    logger.info("\n📊 --- Test Summary ---")
    for lang, status in results.items():
        logger.info(f"{lang.upper()}: {status}")
    
    logger.info("🏁 Multilingual Test Completed")

if __name__ == "__main__":
    asyncio.run(main())
