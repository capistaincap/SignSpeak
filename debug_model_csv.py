import joblib
import pandas as pd
import sys
import os

# Configuration
MODEL_PATH = r"backend\models\signspeak.pkl"
CSV_PATH = r"backend\ml_data\training_data_shivam.csv"
REQUIRED_STABILITY = 5

def debug_model():
    print(f"Loading model from {MODEL_PATH}...")
    try:
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print(f"Loading data from {CSV_PATH}...")
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"Loaded {len(df)} rows.")
    except Exception as e:
        print(f"Failed to load CSV: {e}")
        return

    feature_cols = ['f1', 'f2', 'f3', 'f4', 'ax', 'ay', 'az']
    
    # Check if columns exist
    if not all(col in df.columns for col in feature_cols):
        print(f"Missing columns! Expected {feature_cols}, found {df.columns}")
        return

    print("\n--- Running Predictions ---")
    
    correct_count = 0
    total_count = 0
    
    # Stability Simulation
    last_prediction = ""
    stability_counter = 0
    last_stable_word = ""
    triggered_outputs = []

    # Iterate through data
    for index, row in df.iterrows():
        features = row[feature_cols].values.reshape(1, -1)
        actual_label = row['label']
        
        # Predict
        try:
            prediction = model.predict(pd.DataFrame(features, columns=feature_cols))[0]
        except Exception as e:
            print(f"Prediction error at row {index}: {e}")
            continue

        # Accuracy Check
        if prediction == actual_label:
            correct_count += 1
        total_count += 1

        # Stability Logic (from ml_service.py)
        if prediction == last_prediction:
            stability_counter += 1
        else:
            last_prediction = prediction
            stability_counter = 0

        if stability_counter >= REQUIRED_STABILITY:
            if prediction != last_stable_word:
                last_stable_word = prediction
                triggered_outputs.append((index, prediction))
                stability_counter = 0 # As per some implementations, or it keeps counting? 
                # In ml_service.py: 
                # if prediction != self.last_stable_word:
                #     self.last_stable_word = prediction
                #     self.stability_counter = 0 
                
    
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    print(f"\nTotal Rows: {total_count}")
    print(f"Raw Accuracy: {accuracy:.2f}%")
    
    print("\n--- Stability Simulation Output ---")
    print(f"Number of Triggered Outputs: {len(triggered_outputs)}")
    if len(triggered_outputs) > 0:
        print("First 10 Triggered Outputs:")
        for idx, word in triggered_outputs[:10]:
            print(f"  Row {idx}: {word}")
    else:
        print("NO OUTPUT would be triggered by the system!")
        print("Possible reasons: Predictions are too jittery (instability) or model predicts 'silence'/'noise'.")

    # Sample Predictions
    print("\n--- Sample Predictions (First 20) ---")
    print(f"{'Row':<5} | {'Actual':<10} | {'Predicted':<10} | {'Match'}")
    print("-" * 40)
    for i in range(min(20, len(df))):
        row = df.iloc[i]
        features = row[feature_cols].values.reshape(1, -1)
        pred = model.predict(pd.DataFrame(features, columns=feature_cols))[0]
        actual = row['label']
        match = "✅" if pred == actual else "❌"
        print(f"{i:<5} | {actual:<10} | {pred:<10} | {match}")

if __name__ == "__main__":
    debug_model()
