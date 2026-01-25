import socket
import time
import random
import json

UDP_IP = "127.0.0.1" # Send to Localhost backend
UDP_PORT = 5005

print(f"📡 Starting UDP Test Sender to {UDP_IP}:{UDP_PORT}")
print("This mimics the ESP32 sending sensor data.")
print("Watch your Web Dashboard - you should see values changing!")
print("Press Ctrl+C to stop.\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        # Simulate Flex (0-4095) + Acc (0-10)
        # Format: f1,f2,f3,f4,ax,ay,az
        f1 = random.randint(1000, 3000)
        f2 = random.randint(1000, 3000)
        f3 = random.randint(1000, 3000)
        f4 = random.randint(1000, 3000)
        ax = round(random.uniform(-1, 1), 2)
        ay = round(random.uniform(-1, 1), 2)
        az = round(random.uniform(9, 10), 2)

        message = f"{f1},{f2},{f3},{f4},{ax},{ay},{az}"
        
        sock.sendto(message.encode(), (UDP_IP, UDP_PORT))
        print(f"Sent: {message}")
        
        time.sleep(0.1) # 10Hz

except KeyboardInterrupt:
    print("\nStopped.")
