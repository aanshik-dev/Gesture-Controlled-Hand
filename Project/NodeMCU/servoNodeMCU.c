#include <Servo.h>

Servo indexServo; // Create servo object

void setup() {
  // Matches the 115200 baud rate in your Python script
  Serial.begin(115200);

  indexServo.attach(2); // Connect your servo signal to D4 or GPIO2 of NodeMCU
  indexServo.write(0);  // Initialize at 0 degrees
}

void loop() {
  if (Serial.available() > 0) {
    // Read the string until it hits the newline character '\n'
    String data = Serial.readStringUntil('\n');

    // Convert string to integer
    int angle = data.toInt();

    // Constrain the angle to servo limits (0-180) for safety
    angle = constrain(angle, 0, 180);

    // Move the servo
    indexServo.write(angle);
  }
}