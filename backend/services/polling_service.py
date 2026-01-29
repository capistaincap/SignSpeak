import requests
import threading
import time
import logging
from services.data_store import data_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PollingService:
    def __init__(self, esp_ip="192.168.137.100", interval=0.05):
        self.esp_ip = esp_ip
        self.url = f"http://{self.esp_ip}/data"
        self.interval = interval
        self.running = False
        self.thread = None
        self.on_data_callback = None
        self.session = None

    def register_callback(self, callback):
        self.on_data_callback = callback

    def set_ip(self, ip):
        self.esp_ip = ip
        self.url = f"http://{self.esp_ip}/data"
        logger.info(f"📡 Polling Target Updated: {self.url}")

    def start(self):
        if self.running:
            return

        self.running = True
        self.session = requests.Session()
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"✅ POLLING SERVICE STARTED: Target {self.url}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("POLLING SERVICE STOPPED")

    def _poll_loop(self):
        while self.running:
            start_time = time.time()
            try:
                response = self.session.get(self.url, timeout=0.5)
                if response.status_code == 200:
                    line = response.text.strip()
                    self._process_data(line)
            except requests.exceptions.Timeout:
                pass # Expected if device is sleeping or busy
            except requests.exceptions.ConnectionError:
                # logger.warning(f"⚠️ Connection failed to {self.esp_ip}")
                time.sleep(1) # Backoff
            except Exception as e:
                logger.error(f"❌ Polling Error: {e}")
                time.sleep(1)

            # Sleep to maintain rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            time.sleep(sleep_time)

    def _process_data(self, line):
        try:
            # Expected: f1,f2,f3,f4,ax,ay,az,gx,gy,gz
            parts = line.split(',')
            if len(parts) >= 10:
                vals = [float(x) for x in parts]
                
                flex_vals = vals[0:4]
                acc_vals = vals[4:7]
                gyr_vals = vals[7:10]

                # Update Global Data Store
                data_store.update({
                    "flex": flex_vals,
                    "ax": acc_vals[0], "ay": acc_vals[1], "az": acc_vals[2],
                    "gx": gyr_vals[0], "gy": gyr_vals[1], "gz": gyr_vals[2]
                })

                if self.on_data_callback:
                    self.on_data_callback(flex_vals, acc_vals)
                    
        except ValueError:
            pass # parsing error

# Global instance
polling_service = PollingService()
