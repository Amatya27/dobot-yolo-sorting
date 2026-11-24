import cv2
import time
import argparse
from ultralytics import YOLO
import pydobot
from serial.tools import list_ports

# --- Parse args ---
parser = argparse.ArgumentParser()
parser.add_argument("--simulate", action="store_true", help="Run without robot")
parser.add_argument("--model", type=str, default="yolov8s.pt", help="YOLO model path")
args = parser.parse_args()

# --- YOLO ---
model = YOLO(args.model)

food_classes = [
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
    'hot dog', 'pizza', 'donut', 'cake'
]
vehicle_classes = [
    'car', 'truck', 'bus', 'motorbike', 'bicycle', 'airplane'
]

# --- Robot connect (skip if simulate) ---
device = None
if not args.simulate:
    ports = list_ports.comports()
    if not ports:
        raise RuntimeError("No COM ports found. Connect Dobot.")
    port = ports[-1].device
    print(f"Using Dobot on {port}")
    device = pydobot.Dobot(port=port)

    # Example default coords (update tomorrow)
    home_position = (248, 9, 142, 2)
    food_drop_point = [174, 87, 33, 26]
    vehicle_drop_point = [324, 105, -3, 58]
    source_point = [277, -74, -29, 25]
    above_source_point = [239, -61, 20, -20]

# --- Camera loop ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Camera not found")

print("Press 'q' to quit")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)
    detected_class, category = None, None

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]

            if label in food_classes:
                detected_class, category = label, "food"
            elif label in vehicle_classes:
                detected_class, category = label, "vehicle"

            # Draw detection
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = (0, 255, 0) if category == "food" else \
                    (0, 0, 255) if category == "vehicle" else (255, 255, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Print status
    if category:
        print(f"Detected {detected_class} → {category}")
        if args.simulate:
            print(f"[SIM] Would move to pallet: {category}")
        else:
            device.move_to(*above_source_point)
            device.move_to(*source_point)
            device.suck(True)
            time.sleep(1)
            device.move_to(*home_position)

            if category == "food":
                print(f"Dropping {detected_class} in Pallet A")
                device.move_to(*food_drop_point)
            else:
                print(f"Dropping {detected_class} in Pallet B")
                device.move_to(*vehicle_drop_point)

            device.suck(False)
            device.move_to(*home_position)

        # wait 5s before next
        print("Waiting 5s before next...")
        time.sleep(5)

    cv2.imshow("YOLO Sorting", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if device:
    device.close()
