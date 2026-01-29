import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

# --- PATHS ---
# Relative to where this script is run, or absolute
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'ml_data', 'training_data_shivam.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'signspeak.pkl')

print(f"📂 Data Path: {DATA_PATH}")
print(f"📂 Model Path: {MODEL_PATH}")

# 1. Load the data
print("\nLoading training data...")
# The CSV has a header: f1,f2,f3,f4,ax,ay,az,label
try:
    df = pd.read_csv(DATA_PATH) 
    
    # Verify columns
    expected_cols = ['f1', 'f2', 'f3', 'f4', 'ax', 'ay', 'az', 'label']
    if list(df.columns) != expected_cols:
        print(f"⚠️ Warning: Columns might be different. Expected {expected_cols}, got {list(df.columns)}")
        # If columns match but names are missing, you might need header=None and names=cols
        # But this file HAS a header.

    # Remove duplicates and NaNs
    df = df.dropna()
    # df = df.drop_duplicates() # Optional: sometimes duplicates are okay in sensor data

    print(f"✅ Data loaded: {len(df)} samples")
    print(f"Classes: {df['label'].unique()}")

    # 2. Split Features (X) and Labels (y)
    X = df.drop('label', axis=1)
    y = df['label']

    # 3. Split into Training and Testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Initialize and Train the Random Forest
    print("\nTraining the model (this may take a few seconds)...")
    model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate Accuracy
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    
    print("\n" + "="*30)
    print(f"TRAINING SUCCESSFUL!")
    print(f"Model Accuracy: {acc * 100:.2f}%")
    print("="*30)

    # 6. Save the model to a file
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n✅ Model saved to: {MODEL_PATH}")
    print("Restart your backend to load the new model.")

except FileNotFoundError:
    print(f"❌ ERROR: File not found at {DATA_PATH}")
except Exception as e:
    print(f"❌ An error occurred: {e}")
