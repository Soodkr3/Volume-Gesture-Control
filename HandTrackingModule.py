# HandTrackingModule.py

import cv2
import mediapipe as mp
import math

class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=float(self.detectionCon),
            min_tracking_confidence=float(self.trackCon)
        )

        self.mpDraw = mp.solutions.drawing_utils
        self.lmList = []
        self.results = None

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        """
        Find positions of hand landmarks.
        """
        self.lmList = []  # Initialize lmList as an instance attribute
        bbox = []  # Initialize bbox

        if self.results.multi_hand_landmarks and len(self.results.multi_hand_landmarks) > handNo:
            myHand = self.results.multi_hand_landmarks[handNo]
            xList, yList = [], []

            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

            bbox = [min(xList), min(yList), max(xList), max(yList)]
            if draw:
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                            (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)

        return self.lmList, bbox

    def findDistance(self, p1, p2, img, draw=True):
        """
        Calculate the distance between two points and optionally draw a line and circles.
        
        :param p1: Index of the first point.
        :param p2: Index of the second point.
        :param img: Image frame where the points and line are drawn.
        :param draw: Whether to draw the line and circles on the image.
        :return: Distance between the points, updated image, and line information.
        """
        if len(self.lmList) < max(p1, p2) + 1:
            return 0, img, []

        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

        distance = math.hypot(x2 - x1, y2 - y1)
        return distance, img, [x1, y1, x2, y2, cx, cy]

    def fingersUp(self):
        """
        Determines which fingers are up based on the positions of landmarks.
        Returns a list of integers where 1 indicates the finger is up, and 0 indicates it is down.
        """
        fingers = []
        if not hasattr(self, 'lmList') or len(self.lmList) == 0:
            return fingers  # Return empty list if no landmarks detected

        # Thumb
        # To handle both left and right hands, check if thumb is to the left or right of the previous landmark
        if self.lmList[4][1] > self.lmList[3][1]:  # Right hand
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers (Index, Middle, Ring, Pinky)
        tipIds = [8, 12, 16, 20]
        for id in tipIds:
            # Tip is above pip joint
            if self.lmList[id][2] < self.lmList[id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

def main():
    import time
    cap = cv2.VideoCapture(0)
    detector = handDetector()
    pTime = 0

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image")
            break

        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        if len(lmList) != 0:
            print(lmList[4])  # Accessing the 5th landmark

        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime

        cv2.putText(img, f'FPS: {int(fps)}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
