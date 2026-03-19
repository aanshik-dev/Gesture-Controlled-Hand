import cv2
import mediapipe
import math
import pyfirmata
import numpy
import speech_recognition as sr
import threading
import time

recognizer = sr.Recognizer()
mic = sr.Microphone()
voice_command = ""


# Inform pyfirmata which port to use
my_port = "COM3"
board = pyfirmata.Arduino(my_port)
iter8 = pyfirmata.util.Iterator(board)
iter8.start()

# Pin number of our servo motor is 9
thumb_pin = 3
index_pin = 5
middle_pin = 6
ring_pin = 9
little_pin = 11
servo_thumb = board.get_pin(f"d:{thumb_pin}:s")
servo_idx = board.get_pin(f"d:{index_pin}:s")
servo_mid = board.get_pin(f"d:{middle_pin}:s")
servo_ring = board.get_pin(f"d:{ring_pin}:s")
servo_lit = board.get_pin(f"d:{little_pin}:s")

# Mediapipe drawing and hand detection setup
mp_drawing = mediapipe.solutions.drawing_utils
hand_mpDraw = mediapipe.solutions.drawing_utils
mp_hands = mediapipe.solutions.hands

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


def dist(p1, p2):
    """Calculates Euclidean distance between two points"""
    x1, y1 = p1
    x2, y2 = p2
    return math.hypot(x2 - x1, y2 - y1)


def angle_cal(a, b, c):
    """Calculate angle between three points (b is the vertex)"""
    try:
        bc = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]))
        ba = math.degrees(math.atan2(a[1] - b[1], a[0] - b[0]))
        angle = bc - ba
        angle = angle if angle >= 0 else -1 * angle
        if angle > 180:
            angle = 360 - angle
        return angle
    except Exception as e:
        print(f"Angle error: {e}")
        return 180

def ctrl_type(delta, image):
    color = (0, 0, 255) if delta > 55 else (0, 255, 0)
    text = "Distance Operated" if delta > 55 else "Angle Operated"
    cv2.circle(image, (40, 40), 15, color, cv2.FILLED)
    cv2.putText(image, text, (60, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


def line_cross(a, b, p):
    value = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    return value


def servo_control(len, b2w, t2w, len_fact, delta, ang):
    try:
        if delta > 55:
            if t2w < b2w:
                return 0
            elif t2w > b2w:
                angle = numpy.interp(len, [5, b2w * len_fact], [0, 180])
                constrained_angle = min(max(angle, 0), 180)
                return constrained_angle
            else:
                return 180
        else:
            angle = numpy.interp(ang, [65, 175], [0, 180])
            return angle

    except Exception as e:
        print(f"Servo error: {e}")
        return 180


def thumb_control(a, b, c, p1, p2, delta):
    try:
        angle = angle_cal(a, b, c)
        if delta > 55:
            value1 = line_cross(a, b, p1)
            value2 = line_cross(a, b, p2)
            key = value1 * value2
            if key < 0:
                angle = 0
            angle = numpy.interp(angle, [10, 100], [0, 180])
            return angle
        else:
            angle = numpy.interp(angle, [75, 100], [0, 180])
            return angle
    except Exception as e:
        print(f"Servo error: {e}")
        return 180


def move_servo(servo, angle):
    try:
        constrained_angle = min(max(angle, 0), 180)
        servo.write(constrained_angle)
        return True
    except Exception as e:
        print(f"Servo error: {e}")
        return False


def angle_text(point, angle):
    cv2.putText(
        image,
        str(int(angle)),
        (point[0] - 30, point[1] - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (142, 4, 200),
        2,
        cv2.LINE_AA,
    )


    
# 🎤 Voice command callback
def voice_callback(recognizer, audio):
    global voice_command
    try:
        command = recognizer.recognize_google(audio, language="en-IN").lower()
        print(f"✅ Command received: {command}")
        voice_command = command
    except sr.UnknownValueError:
        print("❓ Couldn't understand audio")
    except sr.RequestError as e:
        print(f"🎤 API error: {e}")
    return ""


# 🎧 Setup background listening
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("🎤 Mic calibrated, starting background listening...")

stop_listening = recognizer.listen_in_background(mic, voice_callback)

with mp_hands.Hands(
    min_detection_confidence=0.5, min_tracking_confidence=0.5, max_num_hands=1
) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Failed to capture image")
            continue
        image = cv2.flip(image, 1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Initialize servo values
        thumb_val = 180
        index_val = 180
        middle_val = 180
        ring_val = 180
        little_val = 180

        if results.multi_hand_landmarks:
            voice_command = ""
            for hand_landmarks in results.multi_hand_landmarks:
                ls = []
                depth = []
                tips = [0, 4, 8, 12, 16, 20]
                try:
                    for idx, lm in enumerate(hand_landmarks.landmark):
                        h, w, c = image.shape
                        x, y = int(lm.x * w), int(lm.y * h)
                        z = lm.z * 1000
                        ls.append((x, y))
                        depth.append(z)
                        if idx in tips:
                            cv2.circle(image, (x, y), 15, (0, 255, 0), cv2.FILLED)

                    if len(ls) > 8:
                        # GET KEY POINTS PROVIDED BY MEDIAPIPE TO OPERATE
                        wrist = ls[0]

                        thumb_root = ls[1]
                        thumb_base = ls[2]
                        thumb_mid = ls[3]
                        thumb_tip = ls[4]

                        idx_base = ls[5]
                        idx_mid = ls[6]
                        idx_tip = ls[8]

                        mid_base = ls[9]
                        mid_mid = ls[10]
                        mid_tip = ls[12]

                        ring_base = ls[13]
                        ring_mid = ls[14]
                        ring_tip = ls[16]

                        lit_base = ls[17]
                        lit_mid = ls[18]
                        lit_tip = ls[20]

                        # Finger Base to wrist distances
                        idx_b2w = dist(idx_base, wrist)
                        mid_b2w = dist(mid_base, wrist)
                        ring_b2w = dist(ring_base, wrist)
                        lit_b2w = dist(lit_base, wrist)

                        # Finger Tip to wrist distances
                        idx_t2w = dist(idx_tip, wrist)
                        mid_t2w = dist(mid_tip, wrist)
                        ring_t2w = dist(ring_tip, wrist)
                        lit_t2w = dist(lit_tip, wrist)

                        # Finger lengths
                        idx_len = dist(idx_base, idx_tip)
                        mid_len = dist(mid_base, mid_tip)
                        ring_len = dist(ring_base, ring_tip)
                        lit_len = dist(lit_base, lit_tip)

                        # Angle calculations
                        index_angle = angle_cal(idx_base, idx_mid, idx_tip)
                        middle_angle = angle_cal(mid_base, mid_mid, mid_tip)
                        ring_angle = angle_cal(ring_base, ring_mid, ring_tip)
                        little_angle = angle_cal(lit_base, lit_mid, lit_tip)

                        # palm tilt detection
                        diff = depth[5] - depth[17]
                        delta = abs(mid_b2w / diff) * 10
                        ctrl_type(delta, image)

                        thumb_val = thumb_control(
                            wrist, idx_base, thumb_tip, thumb_tip, thumb_root, delta
                        )

                        index_val = servo_control(
                            idx_len,
                            idx_b2w,
                            idx_t2w,
                            0.85,
                            delta,
                            index_angle,
                        )
                        middle_val = servo_control(
                            mid_len,
                            mid_b2w,
                            mid_t2w,
                            0.98,
                            delta,
                            middle_angle,
                        )
                        ring_val = servo_control(
                            ring_len,
                            ring_b2w,
                            ring_t2w,
                            0.99,
                            delta,
                            ring_angle,
                        )
                        little_val = servo_control(
                            lit_len,
                            lit_b2w,
                            lit_t2w,
                            0.91,
                            delta,
                            little_angle,
                        )

                        # Debug print
                        print(
                            f"Distances - THUMB:{thumb_val:.0f}, INDEX:{index_val:.0f}, MIDDLE:{middle_val:.0f}, RING:{ring_val:.0f}, LITTLE:{little_val:.0f}"
                        )

                        # Line from wrist to tip
                        cv2.line(image, wrist, thumb_tip, (0, 255, 225), 1)
                        cv2.line(image, wrist, idx_tip, (0, 255, 225), 1)
                        cv2.line(image, wrist, mid_tip, (0, 255, 225), 1)
                        cv2.line(image, wrist, ring_tip, (0, 255, 225), 1)
                        cv2.line(image, wrist, lit_tip, (0, 255, 225), 1)

                        # Lines for angle
                        cv2.line(image, idx_base, thumb_tip, (0, 0, 225), 2)
                        cv2.line(image, idx_mid, idx_tip, (0, 0, 225), 2)
                        cv2.line(image, mid_mid, mid_tip, (0, 0, 225), 2)
                        cv2.line(image, ring_mid, ring_tip, (0, 0, 225), 2)
                        cv2.line(image, lit_mid, lit_tip, (0, 0, 225), 2)

                        angle_text(thumb_tip, int(thumb_val))
                        angle_text(idx_tip, int(index_val))
                        angle_text(mid_tip, int(middle_val))
                        angle_text(ring_tip, int(ring_val))
                        angle_text(lit_tip, int(little_val))

                        mp_drawing.draw_landmarks(
                            image,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            landmark_drawing_spec=hand_mpDraw.DrawingSpec(
                                color=(0, 255, 0)
                            ),
                            connection_drawing_spec=hand_mpDraw.DrawingSpec(
                                color=(255, 0, 0)
                            ),
                        )
                except Exception as e:
                    print(f"Landmark processing error: {e}")
                    continue
        # Voice commands
        elif "one" in voice_command or "1" in voice_command or "ek" in voice_command:
            print("🖐 Showing ONE")
            move_servo(servo_thumb, 180)
            move_servo(servo_idx, 0)
            move_servo(servo_mid, 180)
            move_servo(servo_ring, 180)
            move_servo(servo_lit, 180)
            voice_command = ""

        elif "hello" in voice_command or "hi" in voice_command:
            print("👋 Waving hand")
            for _ in range(2):
                move_servo(servo_thumb, 0)
                move_servo(servo_idx, 0)
                move_servo(servo_mid, 0)
                move_servo(servo_ring, 0)
                move_servo(servo_lit, 0)
                time.sleep(0.5)
                move_servo(servo_thumb, 180)
                move_servo(servo_idx, 180)
                move_servo(servo_mid, 180)
                move_servo(servo_ring, 180)
                move_servo(servo_lit, 180)
                time.sleep(0.5)
            voice_command = ""        
        # Move servos
        if not move_servo(servo_thumb, 180 - thumb_val):
            print("Failed to move index servo")
        if not move_servo(servo_idx, 180 - index_val):
            print("Failed to move index servo")
        if not move_servo(servo_mid, middle_val):
            print("Failed to move middle servo")
        if not move_servo(servo_ring, ring_val):
            print("Failed to move ring servo")
        if not move_servo(servo_lit, little_val):
            print("Failed to move little servo")

        cv2.imshow("Hand Gesture Control", image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
board.exit()
