#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <WiFi.h>
#include <WiFiUdp.h>

Adafruit_MPU6050 mpu;

// ================= WIFI =================
const char* ssid = "ESP32_NET";        // your WiFi / hotspot name
const char* password = "12345678";    // your WiFi password

// ================= UDP ==================
WiFiUDP udp;
const char* laptopIP = "192.168.137.1";   // Laptop / Receiver IP
const int udpPort = 5005;

// ================= FLEX =================
const int flexPins[] = {34, 35, 32, 33}; // Index, Middle, Ring, Pinky
const int FLEX_COUNT = 4;

const int WINDOW_SIZE = 15;
int filterBuffer[FLEX_COUNT][WINDOW_SIZE];
int writeIdx = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n--- SignSpeak Wireless System Starting ---");

  // ===== WiFi Connect =====
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // ===== MPU6050 =====
  if (!mpu.begin()) {
    Serial.println("⚠️ MPU6050 not found! Continuing with Flex only...");
  } else {
    Serial.println("MPU6050 Ready.");
  }

  analogReadResolution(12); // 0–4095

  // ===== Init Filter Buffers =====
  for (int f = 0; f < FLEX_COUNT; f++) {
    int startVal = analogRead(flexPins[f]);
    for (int i = 0; i < WINDOW_SIZE; i++) {
      filterBuffer[f][i] = startVal;
    }
  }
}

int getSmoothFlex(int idx) {
  int raw = analogRead(flexPins[idx]);

  // Flip Middle Finger (GPIO 35)
  if (idx == 1) {
    raw = 4095 - raw;
  }

  filterBuffer[idx][writeIdx] = raw;
  long sum = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) sum += filterBuffer[idx][i];
  return sum / WINDOW_SIZE;
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // ===== CSV Packet =====
  String packet =
    String(getSmoothFlex(0)) + "," +
    String(getSmoothFlex(1)) + "," +
    String(getSmoothFlex(2)) + "," +
    String(getSmoothFlex(3)) + "," +
    String(a.acceleration.x, 3) + "," +
    String(a.acceleration.y, 3) + "," +
    String(a.acceleration.z, 3);

  // ===== Send via UDP =====
  udp.beginPacket(laptopIP, udpPort);
  udp.print(packet);
  udp.endPacket();

  // Debug (optional)
  Serial.println(packet);

  writeIdx = (writeIdx + 1) % WINDOW_SIZE;
  delay(30); // ~33Hz
}
