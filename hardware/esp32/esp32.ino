#include <Wire.h>
#include <MPU6050.h>
#include <WiFi.h>

// ================= WIFI =================
const char* ssid = "ESP32_NET";
const char* password = "12345678";

// ================= MPU =================
MPU6050 mpu(0x68);

// ================= FLEX =================
const int FLEX_COUNT = 4;
const int flexPins[FLEX_COUNT] = {34, 35, 32, 33};

int flexRaw[FLEX_COUNT];
int flexMin[FLEX_COUNT] = {4095, 4095, 4095, 4095};
int flexMax[FLEX_COUNT] = {0, 0, 0, 0};
float flexNorm[FLEX_COUNT];
float flexSmooth[FLEX_COUNT];

// ================= MPU VALUES =================
int16_t ax, ay, az;
int16_t gx, gy, gz;

// Gyro bias
float gyroBiasX = 0, gyroBiasY = 0, gyroBiasZ = 0;

// Smoothed MPU
float accSmooth[3] = {0, 0, 0};
float gyroSmooth[3] = {0, 0, 0};

// ================= PARAMS =================
const float SMOOTH_ALPHA = 0.7;   // higher = smoother
const int GYRO_CALIB_SAMPLES = 300;

// =================================================
void connectWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

// =================================================
void calibrateGyro() {
  Serial.println("GYRO CALIBRATION START - KEEP HAND STILL");

  long sx = 0, sy = 0, sz = 0;

  for (int i = 0; i < GYRO_CALIB_SAMPLES; i++) {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    sx += gx;
    sy += gy;
    sz += gz;
    delay(5);
  }

  gyroBiasX = (float)sx / GYRO_CALIB_SAMPLES;
  gyroBiasY = (float)sy / GYRO_CALIB_SAMPLES;
  gyroBiasZ = (float)sz / GYRO_CALIB_SAMPLES;

  Serial.println("GYRO CALIBRATION DONE");
}

// =================================================
void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("GLOVE START");

  connectWiFi();

  Wire.begin(21, 22);
  delay(100);

  mpu.initialize();
  delay(100);
  mpu.setSleepEnabled(false);
  delay(100);

  calibrateGyro();

  Serial.println("STARTING NORMALIZED STREAM");
  Serial.println("--------------------------------");
}

// =================================================
void loop() {
  // -------- FLEX READ + CALIB --------
  for (int i = 0; i < FLEX_COUNT; i++) {
    flexRaw[i] = analogRead(flexPins[i]);
    flexMin[i] = min(flexMin[i], flexRaw[i]);
    flexMax[i] = max(flexMax[i], flexRaw[i]);

    if (flexMax[i] != flexMin[i]) {
      flexNorm[i] = (float)(flexRaw[i] - flexMin[i]) /
                    (flexMax[i] - flexMin[i]);
    } else {
      flexNorm[i] = 0.0;
    }

    flexNorm[i] = constrain(flexNorm[i], 0.0, 1.0);

    // smoothing
    flexSmooth[i] = SMOOTH_ALPHA * flexSmooth[i] +
                    (1.0 - SMOOTH_ALPHA) * flexNorm[i];
  }

  // -------- MPU READ --------
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // normalize accelerometer (1g ≈ 16384)
  float accX = ax / 16384.0;
  float accY = ay / 16384.0;
  float accZ = az / 16384.0;

  // gyro bias removal + normalization
  float gyroX = (gx - gyroBiasX) / 2000.0;
  float gyroY = (gy - gyroBiasY) / 2000.0;
  float gyroZ = (gz - gyroBiasZ) / 2000.0;

  // smoothing
  accSmooth[0] = SMOOTH_ALPHA * accSmooth[0] + (1 - SMOOTH_ALPHA) * accX;
  accSmooth[1] = SMOOTH_ALPHA * accSmooth[1] + (1 - SMOOTH_ALPHA) * accY;
  accSmooth[2] = SMOOTH_ALPHA * accSmooth[2] + (1 - SMOOTH_ALPHA) * accZ;

  gyroSmooth[0] = SMOOTH_ALPHA * gyroSmooth[0] + (1 - SMOOTH_ALPHA) * gyroX;
  gyroSmooth[1] = SMOOTH_ALPHA * gyroSmooth[1] + (1 - SMOOTH_ALPHA) * gyroY;
  gyroSmooth[2] = SMOOTH_ALPHA * gyroSmooth[2] + (1 - SMOOTH_ALPHA) * gyroZ;

  // -------- OUTPUT (ML FEATURE VECTOR) --------
  Serial.print("FLEX:");
  for (int i = 0; i < FLEX_COUNT; i++) {
    Serial.print(flexSmooth[i], 3);
    if (i < FLEX_COUNT - 1) Serial.print(",");
  }

  Serial.print(" | ACC:");
  Serial.print(accSmooth[0], 3); Serial.print(",");
  Serial.print(accSmooth[1], 3); Serial.print(",");
  Serial.print(accSmooth[2], 3);

  Serial.print(" | GYR:");
  Serial.print(gyroSmooth[0], 3); Serial.print(",");
  Serial.print(gyroSmooth[1], 3); Serial.print(",");
  Serial.print(gyroSmooth[2], 3);

  Serial.println();

  delay(40); // ~25 Hz
}