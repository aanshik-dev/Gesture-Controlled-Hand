# 🐦‍🔥🔥 **🤖 Gesture-Controlled Robotic Hand** 🔥🐦‍🔥

A Python-based system that uses computer vision and speech recognition to control a robotic hand through hand gestures and voice commands.

---

## 📋 Table of Contents

- Project Overview
- Hardware Requirements
- Software Requirements
- Installation
- Hardware Setup
- Code Explanation
- Usage Instructions
- Features
- Troubleshooting
- Credits

---

## 🎯 Project Overview

This project creates an intelligent robotic hand controller that can be operated through:

- **Hand Gestures**: Real-time hand tracking using MediaPipe
- **Voice Commands**: Speech recognition using Azure Cognitive Services
- **Hybrid Control**: Seamless switching between gesture and voice modes

**Main Features:**

- Real-time hand tracking and gesture recognition
- Servo control for 5-fingered robotic hand
- Voice command recognition in English and Hindi
- Visual feedback with OpenCV
- Smooth angle and distance calculations

---

## 🔧 Hardware Requirements

### Main Components:

- [ ] Arduino Uno or similar microcontroller
- [ ] 5x SG90 Servo Motors
- [ ] Robotic hand chassis (3D printed or custom)
- [ ] USB Cable for Arduino
- [ ] 9V Battery or Power Supply (5V for servos)

### Connection Details:

Servo Connections (Arduino):

- Thumb: Pin 3
- Index: Pin 5
- Middle: Pin 6
- Ring: Pin 9
- Little: Pin 11

---

## 💻 Software Requirements

### System Requirements:

- [ ] Python 3.8 - 3.10 (Some libraries may not work with Python 3.14, kindly avoid using it)
- [ ] Windows/Linux/macOS operating system
- [ ] Arduino IDE

### Python Libraries:

- opencv-python
- mediapipe
- numpy
- pyfirmata
- azure-cognitiveservices-speech
- pyserial

### Azure Requirements:

- Azure Cognitive Services Speech Subscription Key
- Azure Region (e.g., "southeastasia")
