import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API Key not found!")
else:
    genai.configure(api_key=api_key)
    print("🔍 List of available models (writing to models_out.txt):")
    try:
        with open("models_out.txt", "w", encoding="utf-8") as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
                    print(f"- {m.name} (written)")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
