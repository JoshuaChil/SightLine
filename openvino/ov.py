from flask import Flask, request, jsonify, Response
import time
import cv2
import numpy as np
from openvino.runtime import Core, Tensor
from groq import Groq

app = Flask(__name__)

# Global variable to store the latest frame
latest_frame = None

# Initialize OpenVINO runtime
ie = Core()
model = ie.read_model(model="best_openvino_model/best_INT8.xml")
compiled_model = ie.compile_model(model=model, device_name="CPU")

input_layer = compiled_model.input(0)
output_layer = compiled_model.output(0)

print("OpenVINO Model loaded successfully")
print("Input shape:", input_layer.shape)
print("Output shape:", output_layer.shape)

# Groq client
client = Groq(api_key="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")

# Class names for your custom model (update based on your model's classes)
class_names = ['bed', 'chair', 'door', 'door-frame', 'shower', 'sink', 'sofa', 'stairs', 'table', 'toilet']

# Global variables for latest inference results
latest_boxes, latest_classes, latest_confidences = None, None, None

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    """Resize and pad image while maintaining aspect ratio."""
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img

def preprocess_image(image):
    """Preprocess image for OpenVINO inference."""
    # Letterbox resize
    img = letterbox(image, new_shape=(640, 640))
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Normalize to [0, 1]
    img = img.astype(np.float32) / 255.0
    
    # Transpose to CHW format
    img = np.transpose(img, (2, 0, 1))
    
    # Add batch dimension
    img = np.expand_dims(img, axis=0)

    img = Tensor(img)
    
    return img

def postprocess_yolo_output(outputs, img_shape, input_shape=(640, 640), conf_threshold=0.25, iou_threshold=0.45):
    """Post-process YOLO output to extract bounding boxes, classes, and confidences."""
    # Assuming YOLO output format: [batch, num_detections, 85] where 85 = 4 (bbox) + 1 (conf) + 80 (classes)
    predictions = outputs[0]  # Get first (and only) batch
    
    boxes = []
    confidences = []
    class_ids = []
    
    # Calculate scale factors for coordinate conversion
    scale_x = img_shape[1] / input_shape[1]
    scale_y = img_shape[0] / input_shape[0]
    
    for detection in predictions:
        scores = detection[5:]  # Class scores start from index 5
        class_id = np.argmax(scores)
        confidence = scores[class_id] * detection[4]  # Object confidence * class score
        
        if confidence > conf_threshold:
            # Convert center coordinates to top-left coordinates
            center_x, center_y, width, height = detection[0:4]
            x = int((center_x - width / 2) * scale_x)
            y = int((center_y - height / 2) * scale_y)
            w = int(width * scale_x)
            h = int(height * scale_y)
            
            boxes.append([x, y, w, h])
            confidences.append(float(confidence))
            class_ids.append(class_id)
    
    # Apply NMS
    if len(boxes) > 0:
        boxes = np.array(boxes)
        confidences = np.array(confidences)
        class_ids = np.array(class_ids)
        
        indices = cv2.dnn.NMSBoxes(boxes.tolist(), confidences.tolist(), conf_threshold, iou_threshold)
        
        if len(indices) > 0:
            indices = indices.flatten()
            return boxes[indices], confidences[indices], class_ids[indices]
    
    return np.array([]), np.array([]), np.array([])

def run_inference(image):
    """Run OpenVINO inference on the image."""
    global latest_boxes, latest_classes, latest_confidences
    
    # Preprocess
    input_blob = preprocess_image(image)
    
    # Create inference request
    infer_request = compiled_model.create_infer_request()
    
    # Set input tensor
    infer_request.set_tensor(input_layer, input_blob)
    
    # Run inference
    infer_request.infer()
    
    # Get output
    output = infer_request.get_tensor(output_layer).data
    
    # Post-process
    boxes, confidences, class_ids = postprocess_yolo_output(output, image.shape)
    
    # Store results globally
    latest_boxes = boxes
    latest_confidences = confidences
    latest_classes = class_ids
    
    return boxes, confidences, class_ids

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
        
        # Convert frame data to OpenCV image for inference
        nparr = np.frombuffer(frame_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is not None:
            # Run inference
            boxes, confidences, class_ids = run_inference(image)
            print(f"Detected {len(boxes)} objects")
            
            # Print detection results
            for i in range(len(boxes)):
                class_name = class_names[class_ids[i]] if class_ids[i] < len(class_names) else f"class_{class_ids[i]}"
                print(f"  {class_name}: {confidences[i]:.2f}")
        
        print(f"Received frame: {len(frame_data)} bytes")
        
        return jsonify({'status': 'success', 'message': 'Frame received and processed'}), 200
        
    except Exception as e:
        print(f"Error processing frame: {str(e)}")
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

@app.route('/get_detections', methods=['GET'])
def get_detections():
    try:
        global latest_boxes, latest_classes, latest_confidences
        
        if latest_boxes is None or len(latest_boxes) == 0:
            return jsonify({'detections': []})
        
        detections = []
        for i in range(len(latest_boxes)):
            class_name = class_names[latest_classes[i]] if latest_classes[i] < len(class_names) else f"class_{latestClasses[i]}"
            detection = {
                'class': class_name,
                'confidence': float(latest_confidences[i]),
                'bbox': {
                    'x': int(latest_boxes[i][0]),
                    'y': int(latest_boxes[i][1]),
                    'width': int(latest_boxes[i][2]),
                    'height': int(latest_boxes[i][3])
                }
            }
            detections.append(detection)
        
        return jsonify({'detections': detections})
        
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
        
        # Access the global frame and detection results
        global latest_frame, latest_boxes, latest_classes, latest_confidences
        frame_available = latest_frame is not None
        detections_available = latest_boxes is not None and len(latest_boxes) > 0
        
        print(f"Frame available: {frame_available}")
        print(f"Detections available: {detections_available}")
        
        if detections_available:
            # Generate context from detections
            detected_objects = []
            for i in range(len(latest_boxes)):
                class_name = class_names[latest_classes[i]] if latest_classes[i] < len(class_names) else f"class_{latest_classes[i]}"
                detected_objects.append({
                    'name': class_name,
                    'confidence': float(latest_confidences[i])
                })
            
            print(f"Current detections: {detected_objects}")
            
            # You can integrate with generate_llm_prompt here if needed
            # prompt = generate_llm_prompt(question, detected_objects)
            
            # For now, create a simple response based on detections
            if detected_objects:
                object_list = ", ".join([obj['name'] for obj in detected_objects])
                response = f"I can see the following objects in the current view: {object_list}. {question}"
            else:
                response = f"No objects detected in the current view. {question}"
        else:
            response = f"No recent detections available. {question}"
        
        # Wait 3 seconds (simulate processing time)
        time.sleep(3)
        
        print("Reply sending")
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': True,
        'input_shape': list(input_layer.shape),
        'output_shape': list(output_layer.shape)
    })

@app.route('/model_info', methods=['GET'])
def model_info():
    return jsonify({
        'input_shape': list(input_layer.shape),
        'output_shape': list(output_layer.shape),
        'device': 'CPU',
        'model_path': 'best_openvino_model/best_INT8.xml',
        'classes': class_names
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
