import threading
import time
import cv2
import torch
from ultralytics import YOLO
from generate_prompt import generate_llm_prompt
from groq import Groq
import depth_pro
import os

device = torch.device("cuda")
model, transform = depth_pro.create_model_and_transforms(device=device, precision=torch.float16)
obj_model = YOLO("yolov8n.pt")
client = Groq(api_key="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")

class_names1 = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 
               'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
               'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 
               'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 
               'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 
               'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 
               'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

class_names2 = ['bed', 'chair', 'door', 'door-frame', 'shower', 'sink', 'sofa', 'stairs', 'table', 'toilet']


cap = cv2.VideoCapture(0)
latest_boxes, latest_classes, latest_depth = None, None, None
IMAGE_PATH = "data/camera.jpg"

def frame_loop():
    global latest_boxes, latest_classes, latest_depth
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            continue

        os.makedirs("data", exist_ok=True)
        cv2.imwrite(IMAGE_PATH, frame)
        print(f"Captured new frame at {IMAGE_PATH}")

        image, _, f_px = depth_pro.load_rgb(IMAGE_PATH)
        image = transform(image).to(device)

        prediction = model.infer(image, f_px=f_px)
        latest_depth = prediction["depth"]
        print(latest_depth.shape())

        results = obj_model(IMAGE_PATH)
        latest_boxes = results[0].boxes
        latest_classes = results[0].boxes.cls.cpu().numpy()

        time.sleep(1)

def input_loop():
    while True:
        question = input("Ask a question (or press Enter to skip): ").strip()
        if not question:
            continue

        if latest_boxes is None or latest_depth is None:
            print("No frame data yet.")
            continue

        llm_prompt = generate_llm_prompt(latest_boxes, latest_classes, latest_depth, class_names2)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": "Context: " + llm_prompt + "\n\nQuestion: " + question}],
            temperature=1,
            max_completion_tokens=256,
            top_p=1,
            stream=True,
            stop=None,
        )

        print("\nAnswer:")
        for chunk in completion:
            print(chunk.choices[0].delta.content or "", end="")
        print("\n")

# Start both threads
threading.Thread(target=frame_loop, daemon=True).start()
input_loop()
