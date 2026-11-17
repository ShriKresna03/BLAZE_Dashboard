// BLAZE firmware skeleton for ESP32-WROOM-32 (Arduino core).
// Libraries: "MAX6675 library" (Adafruit), "ESP32Servo".
//
// Fixes vs. the original snippet:
//  * An open/failed thermocouple returns NaN. NaN >= 500 and NaN < 300 are both
//    false, so the old code fell into "HOLD" and left the valve wherever it was.
//    Now any invalid reading closes the valve (fail-safe).
//  * `volatile` struct copies do not compile; the struct is plain and guarded
//    by the mutex instead.
//  * The mutex was never created.
//  * The servo write is no longer done while holding the mutex.
//  * vTaskDelayUntil keeps a steady 1 s period instead of drifting.
// This is a teaching skeleton. Real LPG hardware also needs an independent
// fail-safe (e.g. normally-closed solenoid, flame/gas sensing, thermal fuse).

#include <Arduino.h>
#include <max6675.h>
#include <ESP32Servo.h>

constexpr int   PIN_SCK = 18, PIN_CS = 23, PIN_SO = 19, PIN_SERVO = 13;
constexpr float T_LOW = 300.0f, T_HIGH = 500.0f;
constexpr int   ANGLE_CLOSED = 0, ANGLE_OPEN = 90;
constexpr uint32_t PERIOD_MS = 1000;

enum class Mode : uint8_t { HEATING, HOLD, SHUTOFF, SENSOR_FAULT };
struct KilnState { float temp; int servoAngle; Mode mode; };

static KilnState        shared = { NAN, ANGLE_CLOSED, Mode::SHUTOFF };
static SemaphoreHandle_t mtx;
static MAX6675          thermocouple(PIN_SCK, PIN_CS, PIN_SO);
static Servo            valve;

static const char* modeName(Mode m) {
  switch (m) {
    case Mode::HEATING: return "HEATING";
    case Mode::HOLD:    return "HOLD";
    case Mode::SHUTOFF: return "SHUTOFF";
    default:            return "SENSOR_FAULT";
  }
}

void controlTask(void*) {            // pinned to Core 1
  int angle = ANGLE_CLOSED;          // boot with the valve closed
  valve.write(angle);
  TickType_t last = xTaskGetTickCount();

  for (;;) {
    float t = thermocouple.readCelsius();
    Mode mode;

    if (isnan(t) || t < 0.0f || t > 1024.0f) {   // open probe / bad read
      angle = ANGLE_CLOSED; mode = Mode::SENSOR_FAULT;
    } else if (t >= T_HIGH) {
      angle = ANGLE_CLOSED; mode = Mode::SHUTOFF;
    } else if (t < T_LOW) {
      angle = ANGLE_OPEN;   mode = Mode::HEATING;
    } else {
      mode = Mode::HOLD;             // between thresholds: keep current angle
    }
    valve.write(angle);

    xSemaphoreTake(mtx, portMAX_DELAY);
    shared = { t, angle, mode };
    xSemaphoreGive(mtx);

    vTaskDelayUntil(&last, pdMS_TO_TICKS(PERIOD_MS));
  }
}

void commsTask(void*) {              // pinned to Core 0
  for (;;) {
    KilnState snap;
    xSemaphoreTake(mtx, portMAX_DELAY);
    snap = shared;
    xSemaphoreGive(mtx);

    // Replace with WebSocket/MQTT later; JSON on Serial is enough to test the dashboard.
    if (isnan(snap.temp))
      Serial.printf("{\"t\":null,\"state\":\"%s\",\"servo\":%d}\n", modeName(snap.mode), snap.servoAngle);
    else
      Serial.printf("{\"t\":%.2f,\"state\":\"%s\",\"servo\":%d}\n", snap.temp, modeName(snap.mode), snap.servoAngle);

    vTaskDelay(pdMS_TO_TICKS(PERIOD_MS));
  }
}

void setup() {
  Serial.begin(115200);
  mtx = xSemaphoreCreateMutex();
  valve.setPeriodHertz(50);
  valve.attach(PIN_SERVO, 500, 2400);
  delay(500);                        // MAX6675 needs ~220 ms before the first valid read

  xTaskCreatePinnedToCore(controlTask, "control", 4096, nullptr, 2, nullptr, 1);
  xTaskCreatePinnedToCore(commsTask,   "comms",   4096, nullptr, 1, nullptr, 0);
}

void loop() { vTaskDelete(nullptr); }
