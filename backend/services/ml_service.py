import joblib
import pandas as pd
import logging
import os
import threading

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self, model_path="models/signspeak.pkl", required_stability=5):
        self.model = None
        self.model_path = model_path

        # Feature order MUST match training
        self.columns = ['f1', 'f2', 'f3', 'f4', 'ax', 'ay', 'az']

        # Stability tracking
        self.last_prediction = None
        self.stability_counter = 0
        self.required_stability = required_stability
        self.last_stable_word = None

        # Callback
        self.on_prediction_callback = None

        # Thread safety (important for FastAPI / sockets)
        self.lock = threading.Lock()

        self._load_model()

    # ---------------- MODEL LOADING ---------------- #
    def _load_model(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, self.model_path)

            if not os.path.exists(full_path):
                logger.error(f"❌ ML Model NOT FOUND at {full_path}")
                return

            self.model = joblib.load(full_path)
            logger.info(f"✅ ML Model loaded from {full_path}")

        except Exception as e:
            logger.exception("❌ Error loading ML model")

    def reload_model(self):
        """Hot reload model without restarting server"""
        logger.info("🔄 Reloading ML model...")
        self._load_model()

    # ---------------- CALLBACK ---------------- #
    def register_callback(self, callback):
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self.on_prediction_callback = callback

    # ---------------- MAIN PREDICTION ---------------- #
    def process_data(self, flex_vals, acc_vals):
        """
        Process sensor data and trigger callback on stable gesture
        flex_vals: [f1, f2, f3, f4]
        acc_vals: [ax, ay, az]
        """

        if not self.model:
            logger.warning("⚠️ Model not loaded")
            return

        if len(flex_vals) != 4 or len(acc_vals) != 3:
            logger.error("❌ Invalid sensor input length")
            return

        try:
            with self.lock:
                features = flex_vals + acc_vals
                df = pd.DataFrame([features], columns=self.columns)

                prediction = self.model.predict(df)[0]
                logger.debug(f"Raw prediction: {prediction}")

                # ---------- Stability Logic ----------
                if prediction == self.last_prediction:
                    self.stability_counter += 1
                else:
                    self.last_prediction = prediction
                    self.stability_counter = 1

                # ---------- Stable Gesture ----------
                if self.stability_counter >= self.required_stability:
                    if prediction != self.last_stable_word:
                        self._emit_prediction(prediction)

        except Exception:
            logger.exception("❌ ML Prediction Error")

    # ---------------- EMIT RESULT ---------------- #
    def _emit_prediction(self, prediction):
        self.last_stable_word = prediction
        self.stability_counter = 0
        self.last_prediction = None

        logger.info(f"🗣️ STABLE GESTURE DETECTED → {prediction}")

        if self.on_prediction_callback:
            try:
                self.on_prediction_callback(prediction)
            except Exception:
                logger.exception("❌ Callback execution failed")


# ---------------- GLOBAL INSTANCE ---------------- #
ml_service = MLService()
