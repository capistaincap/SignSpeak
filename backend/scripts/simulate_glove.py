import socket
import time
import random

# CONFIG
TARGET_IP = "127.0.0.1" # Send to localhost
TARGET_PORT = 6000      # Must match backend port

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"🚀 Sending 50 fake glove packets to {TARGET_IP}:{TARGET_PORT}...")

try:
    for _ in range(50):
        # Simulate Flex Sensors (0-4095)
        f1 = random.randint(2000, 3000)
        f2 = random.randint(2000, 3000)
        f3 = random.randint(2000, 3000)
        f4 = random.randint(2000, 3000)

        # Simulate Accelerometer (-10 to 10)
        ax = round(random.uniform(-5, 5), 2)
        ay = round(random.uniform(-5, 5), 2)
        az = round(random.uniform(9, 10), 2) # Gravity

        # Format: f1,f2,f3,f4,ax,ay,az
        packet = f"{f1},{f2},{f3},{f4},{ax},{ay},{az}"
        
        sock.sendto(packet.encode(), (TARGET_IP, TARGET_PORT))
        print(f"Sent: {packet}")
        
        time.sleep(0.1) # 10Hz

except KeyboardInterrupt:
    print("\n🛑 Stopped.")
