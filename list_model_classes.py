# list_model_classes.py
from ultralytics import YOLO
model = YOLO("yolov8s.pt")
print("Model class names (index: name):")
for idx, name in model.names.items():
    print(f"{idx}: {name}")
