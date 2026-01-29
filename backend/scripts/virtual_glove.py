
import socket
import time
import keyboard
import random

# CONFIG
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
POLL_RATE = 0.1 # 10Hz

# GESTURE MAPPINGS (Approximate Flex Values)
# Format: [f1, f2, f3, f4, ax, ay, az]
gestures = {
    'HELLO': [100, 100, 100, 100, 0, 9, 0],   # Open hand (approx)
    'YES':   [100, 50, 50, 50, 0, 9, 0],      # Thumbs up (approx)
    'NO':    [100, 50, 50, 100, 0, -9, 0],    # Thumbs down (approx)
    'IDLE':  [100, 50, 50, 50, 0, 0, 0]             # Resting
}

print(f"✨ --- Virtual Glove Simulator --- ✨")
print(f"Target: {UDP_IP}:{UDP_PORT}")
print("Controls:")
print("  [H] - Simulate 'HELLO' gesture")
print("  [Y] - Simulate 'YES' gesture")
print("  [N] - Simulate 'NO' gesture")
print("  [Space] - IDLE (Resting)")
print("  [Q] - Quit")
print("-----------------------------------")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
current_gesture = 'IDLE'

try:
    while True:
        # Check inputs
        if keyboard.is_pressed('h'):
            current_gesture = 'HELLO'
        elif keyboard.is_pressed('y'):
            current_gesture = 'YES'
        elif keyboard.is_pressed('n'):
            current_gesture = 'NO'
        elif keyboard.is_pressed('space'):
            current_gesture = 'IDLE'
        elif keyboard.is_pressed('q'):
            print("👋 Exiting...")
            break
            
        # Get target values
        vals = gestures.get(current_gesture, gestures['IDLE'])
        
        # Add slight noise to simulate real sensors
        f1 = vals[0] + random.uniform(-2, 2)
        f2 = vals[1] + random.uniform(-2, 2)
        f3 = vals[2] + random.uniform(-2, 2)
        f4 = vals[3] + random.uniform(-2, 2)
        ax, ay, az = vals[4], vals[5], vals[6]
        
        # Format packet: "f1,f2,f3,f4,ax,ay,az"
        message = f"{f1:.2f},{f2:.2f},{f3:.2f},{f4:.2f},{ax:.2f},{ay:.2f},{az:.2f}"
        
        sock.sendto(message.encode(), (UDP_IP, UDP_PORT))
        
        # print(f"Sent: {current_gesture} -> {message}", end='\r')
        time.sleep(POLL_RATE)

except KeyboardInterrupt:
    print("\n👋 Stop.")
finally:
    sock.close()
