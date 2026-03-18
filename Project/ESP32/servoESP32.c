#include <ESP32Servo.h>

Servo servo;

void setup() {
  Serial.begin(115200);
  servo.attach(18);
}

void loop() {

  if (Serial.available()) {

    int angle = Serial.parseInt();

    if (angle >= 0 && angle <= 180) {
      servo.write(180 - angle);
    }

    Serial.read();
  }
}