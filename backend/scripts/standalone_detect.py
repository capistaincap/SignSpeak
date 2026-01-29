import serial
import joblib
import pyttsx3
import time
import pandas as pd
import warnings
import sys

# 1. Hide the messy warnings
warnings.filterwarnings("ignore", category=UserWarning)

# --- CONFIGURATION ---
PORT = 'COM10'        
BAUD = 115200
MODEL_PATH = '../models/signspeak.pkl'
COLUMNS = ['f1', 'f2', 'f3', 'f4', 'ax', 'ay', 'az'] 

# 2. Initialize Audio
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    print("Step 1: Audio Engine Ready")
except Exception as e:
    print(f"Audio Error: {e}")

# 3. Load Model
try:
    model = joblib.load(MODEL_PATH)
    print(f"Step 2: Model '{MODEL_PATH}' loaded successfully.")
except Exception as e:
    print(f"Step 2 Error: Could not load model. {e}")
    sys.exit()

# 4. Open Serial
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"Step 3: Connected to {PORT}. SYSTEM LIVE!")
except Exception as e:
    print(f"Step 3 Error: Serial Connection Failed. {e}")
    sys.exit()

# --- DETECTION VARIABLES ---
last_spoken = ""
stability_counter = 0
current_guess = ""
REQUIRED_STABILITY = 5 

print("\n*** START SIGNING NOW (HELLO, I, AM, YASH) ***")

try:
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        if line and "," in line:
            parts = line.split(',')
            if len(parts) >= 7:
                # Convert to DataFrame to satisfy Scikit-Learn requirements
                features = [float(x) for x in parts[:7]]
                features_df = pd.DataFrame([features], columns=COLUMNS)
                
                # Prediction
                prediction = model.predict(features_df)[0]
                
                # Stability Logic
                if prediction == current_guess:
                    stability_counter += 1
                else:
                    current_guess = prediction
                    stability_counter = 0
                
                # Action: Speak if word is stable and new
                if stability_counter >= REQUIRED_STABILITY:
                    if prediction != last_spoken:
                        print(f"MESSAGE: {prediction}")
                        engine.say(prediction)
                        engine.runAndWait()
                        last_spoken = prediction
                        stability_counter = 0
                        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    ser.close()