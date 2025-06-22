from flask import Flask, request, jsonify, Response
import time
import threading
import time
import cv2
import torch
from ultralytics import YOLO
from generate_prompt import generate_llm_prompt
from groq import Groq
import depth_pro
import os

app = Flask(__name__)

# Global variable to store the latest frame
latest_frame = None

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

@app.route('/frame', methods=['POST'])
def handle_frame():
    try:
        # Get the raw image data from the request
        frame_data = request.get_data()
        
        if not frame_data:
            return jsonify({'error': 'No frame data received'}), 400
        
        # Store the frame in the global variable
        global latest_frame
        latest_frame = frame_data
        
        print(f"Received frame: {len(frame_data)} bytes")
        
        return jsonify({'status': 'success', 'message': 'Frame received and stored'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_frame', methods=['GET'])
def get_frame():
    try:
        global latest_frame
        
        if latest_frame is None:
            return jsonify({'error': 'No frame available'}), 404
        
        # Return the frame as JPEG image
        return Response(latest_frame, mimetype='image/jpeg')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/question', methods=['POST'])
def handle_question():
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Check if 'question' field exists
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing question field'}), 400
        
        question = data['question']
        
        # Print the question to console
        print(f"Received question: {question}")
        
        # Access the global frame if needed
        global latest_frame
        frame_available = latest_frame is not None
        print(f"Frame available for processing: {frame_available}")
        if frame_available and latest_frame is not None:
            print(f"Frame size: {len(latest_frame)} bytes")
        
        # Wait 3 seconds
        time.sleep(3)
        
        # Return the question in the response field
        print("reply sending")
        return jsonify({'response': question})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
