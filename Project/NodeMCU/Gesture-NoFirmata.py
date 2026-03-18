import cv2
import mediapipe as mp
import math
import numpy as np
import serial
import time

# Serial connection
ser = serial.Serial("COM9",115200)
time.sleep(2)   # allow ESP32 to reset

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)

def dist(p1,p2):
    return math.hypot(p2[0]-p1[0],p2[1]-p1[1])

def angle_cal(a,b,c):

    bc = math.degrees(math.atan2(c[1]-b[1],c[0]-b[0]))
    ba = math.degrees(math.atan2(a[1]-b[1],a[0]-b[0]))

    angle = bc - ba

    if angle < 0:
        angle = -angle

    if angle > 180:
        angle = 360 - angle

    return angle


def servo_control(length,b2w,t2w,factor,delta,angle):

    if delta > 55:

        if t2w < b2w:
            return 0

        elif t2w > b2w:

            value = np.interp(length,[5,b2w*factor],[0,180])
            value = min(max(value,0),180)

            return value

        else:
            return 180

    else:

        value = np.interp(angle,[65,175],[0,180])
        return value


with mp_hands.Hands(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=1
) as hands:

    while cap.isOpened():

        success,image = cap.read()

        if not success:
            continue

        image = cv2.flip(image,1)

        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        results = hands.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                ls = []
                depth = []

                for idx,lm in enumerate(hand_landmarks.landmark):

                    h,w,c = image.shape

                    x,y = int(lm.x*w),int(lm.y*h)
                    z = lm.z*1000

                    ls.append((x,y))
                    depth.append(z)

                wrist = ls[0]

                idx_base = ls[5]
                idx_mid = ls[6]
                idx_tip = ls[8]

                mid_base = ls[9]

                idx_b2w = dist(idx_base,wrist)
                idx_t2w = dist(idx_tip,wrist)
                idx_len = dist(idx_base,idx_tip)

                mid_b2w = dist(mid_base,wrist)

                index_angle = angle_cal(idx_base,idx_mid,idx_tip)

                diff = depth[5] - depth[17]
                delta = abs(mid_b2w/diff)*10 if diff!=0 else 0

                index_val = servo_control(
                    idx_len,
                    idx_b2w,
                    idx_t2w,
                    0.85,
                    delta,
                    index_angle
                )

                servo_angle = int(index_val)

                # send to ESP32
                ser.write((str(servo_angle) + "\n").encode())

                print("Servo:",servo_angle)

                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

        cv2.imshow("Hand Tracking",image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        time.sleep(0.03)   # prevent serial flooding

cap.release()
cv2.destroyAllWindows()
ser.close()