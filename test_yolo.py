# test_yolo.py
import cv2
from ultralytics import YOLO
model = YOLO("yolov8s.pt")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Cannot open camera")
while True:
    ret, frame = cap.read()
    if not ret:
        continue
    results = model(frame, verbose=False)[0]
    out = frame if results.boxes is None or len(results.boxes)==0 else results.plot()
    cv2.imshow("YOLO Test - ESC to exit", out)
    if cv2.waitKey(1) & 0xFF == 27:
        break
cap.release()
cv2.destroyAllWindows()
