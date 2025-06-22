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
import tempfile
import uuid
import numpy as np

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
IMAGE_PATH = "camera.jpg"


def save_frame_to_temp_file(frame_bytes):
    filename = f"frame_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join("tmp", filename)  # Ensure 'tmp/' exists
    with open(filepath, "wb") as f:
        f.write(frame_bytes)
    return filepath

@app.route('/frame', methods=['POST'])
def handle_frame():
    try:
        # Get the raw image data from the request
        frame_data = request.get_data()

        if not frame_data:
            return jsonify({'error': 'No frame data received'}), 400

        # Convert bytes to NumPy array and decode image
        np_arr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image data'}), 400

        # Rotate the image 90 degrees clockwise
        rotated_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

        # Encode the rotated image back to bytes
        success, encoded_img = cv2.imencode('.jpg', rotated_img)
        if not success:
            return jsonify({'error': 'Failed to encode image'}), 500

        # Store the rotated image in the global variable
        global latest_frame
        latest_frame = encoded_img.tobytes()

        print(f"Received and rotated frame: {len(latest_frame)} bytes")

        return jsonify({'status': 'success', 'message': 'Frame received, rotated, and stored'}), 200

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
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing question field'}), 400

        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Question is empty'}), 400

        frame_path = save_frame_to_temp_file(latest_frame)

        image, _, f_px = depth_pro.load_rgb(frame_path)
        image = transform(image).to(device)

        prediction = model.infer(image, f_px=f_px)
        latest_depth = prediction["depth"]

        results = obj_model(frame_path)
        latest_boxes = results[0].boxes
        latest_classes = results[0].boxes.cls.cpu().numpy()
        # Check that all necessary frame data is available
        if latest_boxes is None or latest_depth is None or latest_classes is None:
            return jsonify({'error': 'Frame data not available'}), 503

        # Generate prompt
        llm_prompt = generate_llm_prompt(latest_boxes, latest_classes, latest_depth, class_names1)

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": f"Context: {llm_prompt}\n\nQuestion: {question}"}],
            temperature=1,
            max_completion_tokens=256,
            top_p=1,
            stream=False,
            stop=None,
        )

        # stream=False → no delta → use `.message.content`
        content = completion.choices[0].message.content
        if content:
            return jsonify({'response': content})
        else:
            return jsonify({'response': "Error: Please ask again"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)