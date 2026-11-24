# webcam_test.py
import cv2
cap = cv2.VideoCapture(0)  # try 1 or 2 if 0 doesn't work
if not cap.isOpened():
    raise SystemExit("Cannot open camera (try index 1 or 2)")
ret, frame = cap.read()
if not ret:
    raise SystemExit("Cannot read frame from camera")
cv2.imshow("Webcam Test - press any key", frame)
cv2.waitKey(0)
cap.release()
cv2.destroyAllWindows()
