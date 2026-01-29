#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ================= WIFI CONFIG =================
const char* WIFI_SSID = "ESP32_NET";
const char* WIFI_PASS = "12345678";

// CRITICAL: Updated for Laptop Hotspot
const char* SERVER_IP = "192.168.137.1";   // Laptop Hotspot Default IP
const int SERVER_PORT = 5005;

// ================= SENSORS =================
Adafruit_MPU6050 mpu;
WiFiUDP udp;

// ================= FLEX CONFIG =================
const int flexPins[] = {34, 35, 32, 33};
const int WINDOW_SIZE = 15;
int filterBuffer[4][WINDOW_SIZE];
int writeIdx = 0;

// ================= FLEX FILTER =================
int getSmoothFlex(int idx) {
  int raw = analogRead(flexPins[idx]);
  
  // Keep your specific logic: Middle finger (idx 1) is flipped
  if (idx == 1) raw = 4095 - raw;

  filterBuffer[idx][writeIdx] = raw;
  long sum = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) sum += filterBuffer[idx][i];
  return sum / WINDOW_SIZE;
}

// ================= WIFI CONNECT =================
void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("=== SignSpeak WIRELESS MODE (UDP) ===");

  // ---- MPU INIT (Adafruit Style) ----
  if (!mpu.begin()) {
    Serial.println("❌ MPU6050 Connection Failed");
  } else {
    Serial.println("✅ MPU6050 OK");
  }

  // ---- FLEX INIT ----
  analogReadResolution(12);
  for (int f = 0; f < 4; f++) {
    int v = analogRead(flexPins[f]);
    for (int i = 0; i < WINDOW_SIZE; i++) {
      filterBuffer[f][i] = v;
    }
  }

  // ---- WIFI ----
  connectWiFi();
  udp.begin(SERVER_PORT);
}

// ================= LOOP =================
void loop() {
  // Maintain WiFi Connection
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Get Sensor Data
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  int f1 = getSmoothFlex(0);
  int f2 = getSmoothFlex(1);
  int f3 = getSmoothFlex(2);
  int f4 = getSmoothFlex(3);

  // CSV packet for backend (Precise format from Code 1)
  String packet =
    String(f1) + "," +
    String(f2) + "," +
    String(f3) + "," +
    String(f4) + "," +
    String(a.acceleration.x) + "," +
    String(a.acceleration.y) + "," +
    String(a.acceleration.z);

  // Serial (debug)
  Serial.println(packet);

  // UDP send
  udp.beginPacket(SERVER_IP, SERVER_PORT);
  udp.print(packet);
  udp.endPacket();

  writeIdx = (writeIdx + 1) % WINDOW_SIZE;
  delay(30);   // ~33 Hz
}
