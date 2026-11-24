import cv2
from ultralytics import YOLO
import time
from serial.tools import list_ports
import pydobot

# --- Find available COM ports ---
available_ports = list_ports.comports()
print(f'Available ports: {[x.device for x in available_ports]}')
if not available_ports:
    raise Exception("No Dobot found. Connect robot via USB and power it ON.")
port = available_ports[-1].device  # pick last one (usually Dobot)
print(f"Using port: {port}")

# --- Connect Dobot ---
device = pydobot.Dobot(port=port)

# --- Define positions (example numbers, update in lab) ---
home_position = (240.6, 0, 150.6, 0)

food_drop_point = [236.2, -150.4, 22.0, -32.5]       # Pallet A
vehicle_drop_point = [253.2, 68.1, 20.6, 15.0]       # Pallet B

pick_up = [258.70147705078125, -36.22687530517578, -26.21624183654785, -7.971493721008301]                # pickup (touching card)
hover_pick = [245.6, -34.3, 20.0, -7.9]              # hover above card

device.move_to(*home_position)
time.sleep(2)

# --- Load YOLO ---
model = YOLO("yolov8s.pt")

food_classes = [
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
    'hot dog', 'pizza', 'donut', 'cake'
]
vehicle_classes = [
    'car', 'truck', 'bus', 'motorbike', 'bicycle', 'airplane'
]

def check_class():
    """Run YOLO for up to 5s and return (name, category)"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None, None

    time.sleep(1)
    tstart = time.time()
    best_conf = 0
    detected_class, category = None, None

    while True:
        if time.time() - tstart > 5:
            break

        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)

        # Loop over detections
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                conf = float(box.conf[0])

                # Debug print
                print(f"Detected {label} ({conf:.2f})")

                if conf < 0.45:  # ignore weak predictions
                    continue

                if label in food_classes and conf > best_conf:
                    detected_class, category = label, "food"
                    best_conf = conf
                elif label in vehicle_classes and conf > best_conf:
                    detected_class, category = label, "vehicle"
                    best_conf = conf

                # Draw bounding box
                color = (0, 255, 0) if category == "food" else \
                        (0, 0, 255) if category == "vehicle" else (255, 0, 0)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        status = category if category else "ignored"
        cv2.putText(frame, f"Class: {status}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
        cv2.imshow("Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if category:
            break

    cap.release()
    cv2.destroyAllWindows()
    return detected_class, category

def go_to_hover():
    # Hover above card
    device.move_to(*hover_pick)
    time.sleep(1)

    obj_name, category = check_class()
    if category not in ("food", "vehicle"):
        print("No valid object detected, skipping...")
        return

    print(f"Detected: {obj_name} → {category}. Moving to pick up...")

    # Move down to pick
    device.move_to(*pick_up)
    device.suck(True)
    time.sleep(1.5)   # hold suction longer
    device.move_to(*hover_pick)

    # Move to home before drop
    device.move_to(*home_position)

    # Drop at correct pallet
    if category == "food":
        print(f"Dropping {obj_name} in Pallet A (food)")
        device.move_to(*food_drop_point)
    else:
        print(f"Dropping {obj_name} in Pallet B (vehicle)")
        device.move_to(*vehicle_drop_point)

    device.suck(False)
    time.sleep(1)
    device.move_to(*home_position)
    
    # ✅ Lower Z for next card
    pick_up[2] -= 8
    hover_pick[2] = pick_up[2] + 40
    print(f"Next pickup Z adjusted to {pick_up[2]:.2f}")

    

if __name__ == "__main__":
    for _ in range(6):
        go_to_hover()
    device.move_to(*home_position)
    device.close()
