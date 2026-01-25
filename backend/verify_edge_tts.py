# verify_edge_tts.py
import asyncio
import edge_tts
import os

async def test_stream():
    print("Testing Edge TTS Streaming...")
    voice = "en-US-ChristopherNeural"
    text = "Hello, this is a streaming test."
    communicate = edge_tts.Communicate(text, voice)
    
    mp3_data = b""
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_data += chunk["data"]
        
        print(f"✅ Stream Success! Received {len(mp3_data)} bytes.")
        
        with open("test_stream.mp3", "wb") as f:
            f.write(mp3_data)
        print("✅ Saved to test_stream.mp3. Try playing it.")
        
    except Exception as e:
        print(f"❌ Stream Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_stream())
