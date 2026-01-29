import serial
import serial.tools.list_ports
import threading
import time
import logging
from services.data_store import data_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerialService:
    def __init__(self, port=None, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.on_data_callback = None # Callback function(flex_vals, acc_vals)

    def register_callback(self, callback):
        """Register a function to be called when valid data is received"""
        self.on_data_callback = callback

    def _find_esp32_port(self):
        """Auto-detect a likely ESP32/Arduino port"""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            # Look for common USB-Serial descriptions
            if "USB" in p.description or "Serial" in p.description or "CP210" in p.description or "CH340" in p.description:
                return p.device
        # Fallback to first available if any
        if ports:
            return ports[0].device
        return None # Return None if no ports found

    def start(self):
        if self.running:
            return
        
        target_port = self.port if self.port else self._find_esp32_port()
        
        if not target_port:
            logger.info("⚠️ No Serial ports found. Serial service skipped (Wireless Mode).")
            return

        try:
            self.ser = serial.Serial(target_port, self.baud_rate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            logger.info(f"✅ SERIAL CONNECTED: {target_port} @ {self.baud_rate}")
        except PermissionError:
             logger.warning(f"⚠️ Serial port {target_port} busy or unavailable (Access Denied). Continuing in Wireless Mode.")
        except serial.SerialException as e:
            logger.error(f"❌ SERIAL ERROR: Could not connect to {target_port}: {e}")
            # Try to list available ports to help user
            ports = [p.device for p in serial.tools.list_ports.comports()]
            logger.info(f"Available ports: {ports}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.ser:
            self.ser.close()

    def _read_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                # Expecting format: "f1,f2,f3,f4,ax,ay,az" (7 values)
                if "," in line:
                    parts = line.split(',')
                    if len(parts) >= 7:
                        # Parse values
                        vals = [float(x) for x in parts[:7]]
                        
                        flex_vals = vals[0:4]
                        acc_vals = vals[4:7] # ax, ay, az

                        # Update Global Data Store (Legacy support for frontend)
                        data_store.update({
                            "flex": flex_vals,
                            "ax": acc_vals[0], "ay": acc_vals[1], "az": acc_vals[2],
                            # Zero out gyro/others if not present in this format
                            "gx": 0, "gy": 0, "gz": 0
                        })

                        # Trigger Callback for ML
                        if self.on_data_callback:
                            self.on_data_callback(flex_vals, acc_vals)

            except (ValueError, IndexError):
                continue # Ignore parse errors (common during startup)
            except serial.SerialException:
                logger.error("Serial connection lost")
                break
            except Exception as e:
                logger.error(f"Error in serial loop: {e}")
                time.sleep(1)

# Global instance
serial_service = SerialService()
