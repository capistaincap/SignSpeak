import joblib
import pandas as pd
import logging
import os
import sys

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self, model_path="models/signspeak.pkl"):
        self.model = None
        self.model_path = model_path
        self.columns = ['f1', 'f2', 'f3', 'f4', 'ax', 'ay', 'az']
        
        # Stability tracking
        self.last_prediction = ""
        self.stability_counter = 0
        self.required_stability = 5
        self.last_stable_word = ""
        
        # Callbacks
        self.on_prediction_callback = None # Function(word)

        self._load_model()

    def _load_model(self):
        try:
            # Handle relative paths safely
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, self.model_path)
            
            if os.path.exists(full_path):
                self.model = joblib.load(full_path)
                logger.info(f"✅ ML Model loaded from {full_path}")
            else:
                logger.error(f"❌ ML Model NOT FOUND at {full_path}")
        except Exception as e:
            logger.error(f"❌ Error loading ML model: {e}")

    def register_callback(self, callback):
        self.on_prediction_callback = callback

    def process_data(self, flex_vals, acc_vals):
        """
        Process sensor data and return prediction if stable
        """
        if not self.model:
            return

        try:
            # Combine into feature vector
            features = flex_vals + acc_vals # [f1, f2, f3, f4, ax, ay, az]
            
            # DataFrame for sklearn
            features_df = pd.DataFrame([features], columns=self.columns)
            
            # Predict
            prediction = self.model.predict(features_df)[0]
            
            # Debug: Print raw prediction to see if model is working
            # print(f"Raw ML: {prediction}") 
            
            # Stability Logic
            if prediction == self.last_prediction:
                self.stability_counter += 1
            else:
                self.last_prediction = prediction
                self.stability_counter = 0

            # Trigger Action on Stability
            if self.stability_counter >= self.required_stability:
                # Only trigger if it's a NEW stable word (debouncing repetitions)
                if prediction != self.last_stable_word:
                    self.last_stable_word = prediction
                    self.stability_counter = 0 # Reset to require re-stabilization or keep it high? 
                    # Original logic reset it, but technically if I hold 'A', it stays 'A'
                    # If I want to speak 'A' again, I need to break gesture.
                    # Implementing "Edge Trigger":
                    
                    if self.on_prediction_callback:
                        self.on_prediction_callback(prediction)
                    
                    logger.info(f"🗣️ DETECTED: {prediction}")

        except Exception as e:
            logger.error(f"ML Prediction Error: {e}")

# Global Instance
ml_service = MLService()
