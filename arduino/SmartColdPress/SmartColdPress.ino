/*
  Smart Cold-Press Management System
  Arduino UNO V3 firmware

  Sensors:
    pH analog output -> A0
    UV sensor output -> A1

  Optional:
    UV-C relay/control -> D7

  Serial output:
  device_ms,ph_raw,ph_voltage,ph,uv_raw,uv_voltage,uv_mw_cm2,uv_on

  IMPORTANT:
  - Recalibrate PH_SLOPE / PH_INTERCEPT using your actual pH module.
  - Recalibrate UV_SLOPE / UV_INTERCEPT using your actual UV sensor.
  - The UV sensor is positioned to measure lamp intensity ABOVE the juice container.
  - UV-C can injure skin and eyes. Use a closed chamber and proper interlocks.
*/

const int PH_PIN = A0;
const int UV_PIN = A1;
const int UV_RELAY_PIN = 7;

// UNO ADC
const float ADC_REF_V = 5.0;
const float ADC_MAX = 1023.0;

// -------- pH calibration --------
// pH = PH_SLOPE * sensor_voltage + PH_INTERCEPT
// Replace these values after calibration.
float PH_SLOPE = -5.70;
float PH_INTERCEPT = 21.34;

// -------- UV calibration --------
// UV intensity (mW/cm^2) = UV_SLOPE * sensor_voltage + UV_INTERCEPT
// Default values are placeholders. Calibrate with your UV meter.
float UV_SLOPE = 1.0;
float UV_INTERCEPT = 0.0;

// Relay behavior.
// Many relay modules are active LOW. Change if needed.
const bool RELAY_ACTIVE_LOW = true;

// Set true only if your UV-C lamp is actually controlled through a safe,
// isolated relay/interface.
const bool ENABLE_UV_RELAY_CONTROL = false;

unsigned long lastSample = 0;
const unsigned long SAMPLE_MS = 1000;

int readAveragedAnalog(int pin, int samples = 20) {
  long total = 0;
  for (int i = 0; i < samples; i++) {
    total += analogRead(pin);
    delay(3);
  }
  return (int)(total / samples);
}

void setUVRelay(bool on) {
  if (!ENABLE_UV_RELAY_CONTROL) return;
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(UV_RELAY_PIN, on ? LOW : HIGH);
  } else {
    digitalWrite(UV_RELAY_PIN, on ? HIGH : LOW);
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(UV_RELAY_PIN, OUTPUT);
  setUVRelay(false);

  delay(500);
  Serial.println("device_ms,ph_raw,ph_voltage,ph,uv_raw,uv_voltage,uv_mw_cm2,uv_on");
}

void loop() {
  if (millis() - lastSample < SAMPLE_MS) return;
  lastSample = millis();

  int phRaw = readAveragedAnalog(PH_PIN);
  int uvRaw = readAveragedAnalog(UV_PIN);

  float phVoltage = phRaw * ADC_REF_V / ADC_MAX;
  float uvVoltage = uvRaw * ADC_REF_V / ADC_MAX;

  float phValue = PH_SLOPE * phVoltage + PH_INTERCEPT;
  float uvIntensity = UV_SLOPE * uvVoltage + UV_INTERCEPT;
  if (uvIntensity < 0) uvIntensity = 0;

  // In the basic prototype, "UV on" is inferred from detected intensity.
  // Adjust the threshold after measuring your lamp and sensor background.
  bool uvOn = uvRaw > 20;

  Serial.print(millis());
  Serial.print(",");
  Serial.print(phRaw);
  Serial.print(",");
  Serial.print(phVoltage, 4);
  Serial.print(",");
  Serial.print(phValue, 3);
  Serial.print(",");
  Serial.print(uvRaw);
  Serial.print(",");
  Serial.print(uvVoltage, 4);
  Serial.print(",");
  Serial.print(uvIntensity, 4);
  Serial.print(",");
  Serial.println(uvOn ? 1 : 0);
}
