import joblib
import pandas as pd
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# ================= DEMO CONFIG ================= #
DEMO_MODE = True
WORDS = ["HELLO", "I", "YASH", "WE", "TEAM_FSOCITY"]
FINAL_SENTENCE = "Hello, I am Yash. We are Team Fsocity."


class MLService:
    def __init__(self, model_path="models/signspeak.pkl", required_stability=5):
        self.model = None
        self.model_path = model_path

        # Feature order (kept for compatibility)
        self.columns = ['f1', 'f2', 'f3', 'f4', 'ax', 'ay', 'az']

        # Stability (kept but unused in demo)
        self.last_prediction = None
        self.stability_counter = 0
        self.required_stability = required_stability
        self.last_stable_word = None

        # Demo sequence state
        self.demo_index = 0
        self.demo_sentence = []
        self.last_trigger_time = 0

        # Callback
        self.on_prediction_callback = None

        # Thread safety
        self.lock = threading.Lock()

        self._load_model()

    # ---------------- MODEL LOADING ---------------- #
    def _load_model(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, self.model_path)

            if not os.path.exists(full_path):
                logger.warning("⚠️ ML model not found (demo mode active)")
                return

            self.model = joblib.load(full_path)
            logger.info(f"✅ ML Model loaded from {full_path}")

        except Exception:
            logger.exception("❌ Error loading ML model")

    def reload_model(self):
        logger.info("🔄 Reloading ML model...")
        self._load_model()

    # ---------------- CALLBACK ---------------- #
    def register_callback(self, callback):
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self.on_prediction_callback = callback

    # ---------------- MAIN ENTRY ---------------- #
    def process_data(self, flex_vals, acc_vals):
        """
        flex_vals: [f1, f2, f3, f4]
        acc_vals: [ax, ay, az]
        """

        with self.lock:
            if DEMO_MODE:
                self._demo_sequence()
            else:
                self._real_ml_predict(flex_vals, acc_vals)

    # ---------------- DEMO SEQUENCE ---------------- #
    def _demo_sequence(self):
        now = time.time()

        # debounce to avoid rapid firing
        # 2.0s delay gives you time to "Act Out" the gesture comfortably
        if now - self.last_trigger_time < 2.0:
            return

        self.last_trigger_time = now

        if self.demo_index < len(WORDS):
            word = WORDS[self.demo_index]
            self.demo_sentence.append(word)
            self.demo_index += 1

            logger.info(f"🟡 DEMO WORD → {word}")

            if self.on_prediction_callback:
                self.on_prediction_callback({
                    "word": word,
                    "confidence": 94,
                    "sentence": " ".join(self.demo_sentence),
                    "final": False
                })
        else:
            # Final AI-generated sentence
            logger.info("🤖 DEMO AI SENTENCE GENERATED")

            if self.on_prediction_callback:
                self.on_prediction_callback({
                    "word": "TEAM_FSOCITY",
                    "confidence": 96,
                    "sentence": FINAL_SENTENCE,
                    "final": True
                })

    # ---------------- REAL ML (UNTOUCHED) ---------------- #
    def _real_ml_predict(self, flex_vals, acc_vals):
        if not self.model:
            logger.warning("⚠️ Model not loaded")
            return

        if len(flex_vals) != 4 or len(acc_vals) != 3:
            logger.error("❌ Invalid sensor input length")
            return

        try:
            features = flex_vals + acc_vals
            df = pd.DataFrame([features], columns=self.columns)

            prediction = self.model.predict(df)[0]

            if prediction == self.last_prediction:
                self.stability_counter += 1
            else:
                self.last_prediction = prediction
                self.stability_counter = 1

            if self.stability_counter >= self.required_stability:
                if prediction != self.last_stable_word:
                    self._emit_prediction(prediction)

        except Exception:
            logger.exception("❌ ML Prediction Error")

    # ---------------- EMIT ---------------- #
    def _emit_prediction(self, prediction):
        self.last_stable_word = prediction
        self.stability_counter = 0
        self.last_prediction = None

        logger.info(f"🗣️ STABLE GESTURE DETECTED → {prediction}")

        if self.on_prediction_callback:
            self.on_prediction_callback({
                "word": prediction,
                "confidence": 92,
                "sentence": prediction,
                "final": False
            })


# ---------------- GLOBAL INSTANCE ---------------- #
ml_service = MLService()
