from flask import Flask, request, jsonify, Response
import time
import cv2
import numpy as np
from openvino.runtime import Core, Tensor
from groq import Groq

app = Flask(__name__)

latest_frame = None

ie = Core()
model = ie.read_model(model="best_openvino_model/best_INT8.xml")
compiled_model = ie.compile_model(model=model, device_name="CPU")

input_layer = compiled_model.input(0)
output_layer = compiled_model.output(0)

print("OpenVINO Model loaded successfully")
print("Input shape:", input_layer.shape)
print("Output shape:", output_layer.shape)

client = Groq(api_key="")

class_names = ['bed', 'chair', 'door', 'door-frame', 'shower', 'sink', 'sofa', 'stairs', 'table', 'toilet']

latest_boxes, latest_classes, latest_confidences = None, None, None

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img

def preprocess_image(image):
    img = letterbox(image, new_shape=(640, 640))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    img = Tensor(img)
    print(f"Preprocessed image shape: {img.shape}")  # Debug
    return img

def postprocess_yolo_output(outputs, img_shape, input_shape=(640, 640), conf_threshold=0.25, iou_threshold=0.45):
    predictions = outputs[0]
    print(f"Raw output predictions shape: {predictions.shape}")  # Debug

    boxes = []
    confidences = []
    class_ids = []

    scale_x = img_shape[1] / input_shape[1]
    scale_y = img_shape[0] / input_shape[0]

    for detection in predictions:
        scores = detection[5:]
        print(f"Class scores: {scores}")  # Debug
        class_id = np.argmax(scores)
        print(f"Selected class_id: {class_id}")  # Debug
        confidence = scores[class_id] * detection[4]
        print(f"Calculated confidence: {confidence}")  # Debug

        if confidence > conf_threshold:
            center_x, center_y, width, height = detection[0:4]
            x = int((center_x - width / 2) * scale_x)
            y = int((center_y - height / 2) * scale_y)
            w = int(width * scale_x)
            h = int(height * scale_y)
            boxes.append([x, y, w, h])
            confidences.append(float(confidence))
            class_ids.append(class_id)

    if len(boxes) > 0:
        boxes = np.array(boxes)
        confidences = np.array(confidences)
        class_ids = np.array(class_ids)
        indices = cv2.dnn.NMSBoxes(boxes.tolist(), confidences.tolist(), conf_threshold, iou_threshold)
        print(f"NMS indices: {indices}")  # Debug

        if len(indices) > 0:
            indices = indices.flatten()
            filtered_boxes = boxes[indices]
            filtered_confidences = confidences[indices]
            filtered_class_ids = class_ids[indices]
            print(f"Filtered boxes: {filtered_boxes}")  # Debug
            print(f"Filtered confidences: {filtered_confidences}")  # Debug
            print(f"Filtered class_ids: {filtered_class_ids}")  # Debug
            return filtered_boxes, filtered_confidences, filtered_class_ids

    return np.array([]), np.array([]), np.array([])

def run_inference(image):
    global latest_boxes, latest_classes, latest_confidences

    input_blob = preprocess_image(image)

    infer_request = compiled_model.create_infer_request()
    infer_request.set_tensor(input_layer, input_blob)

    infer_request.infer()

    output = infer_request.get_tensor(output_layer).data
    print(f"Raw model output shape: {output.shape}")  # Debug

    boxes, confidences, class_ids = postprocess_yolo_output(output, image.shape)
    print(f"Post-processed boxes: {boxes}, confidences: {confidences}, class_ids: {class_ids}")  # Debug

    latest_boxes = boxes
    latest_confidences = confidences
    latest_classes = class_ids

    return boxes, confidences, class_ids

@app.route('/frame', methods=['POST'])
def handle_frame():
    try:
        frame_data = request.get_data()

        if not frame_data:
            return jsonify({'error': 'No frame data received'}), 400

        global latest_frame
        latest_frame = frame_data

        nparr = np.frombuffer(frame_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is not None:
            boxes, confidences, class_ids = run_inference(image)
            print(f"Detected {len(boxes)} objects")

            for i in range(len(boxes)):
                if class_ids[i] < len(class_names):
                    class_name = class_names[class_ids[i]]
                else:
                    class_name = f"class_{class_ids[i]}"
                print(f"  {class_name}: {confidences[i]:.2f}")

        print(f"Received frame data size: {len(frame_data)} bytes")

        return jsonify({'status': 'success', 'message': 'Frame received and processed'}), 200

    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_frame', methods=['GET'])
def get_frame():
    try:
        global latest_frame
        if latest_frame is None:
            return jsonify({'error': 'No frame available'}), 404
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
            class_name = class_names[latest_classes[i]] if latest_classes[i] < len(class_names) else f"class_{latest_classes[i]}"
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
        data = request.get_json()

        if not data or 'question' not in data:
            return jsonify({'error': 'Missing question field'}), 400

        question = data['question']

        print(f"Received question: {question}")

        global latest_frame, latest_boxes, latest_classes, latest_confidences
        frame_available = latest_frame is not None
        detections_available = latest_boxes is not None and len(latest_boxes) > 0

        print(f"Frame available: {frame_available}")
        print(f"Detections available: {detections_available}")

        if detections_available:
            detected_objects = []
            for i in range(len(latest_boxes)):
                class_name = class_names[latest_classes[i]] if latest_classes[i] < len(class_names) else f"class_{latest_classes[i]}"
                detected_objects.append({
                    'name': class_name,
                    'confidence': float(latest_confidences[i])
                })

            print(f"Current detections: {detected_objects}")

            if detected_objects:
                object_list = ", ".join([obj['name'] for obj in detected_objects])
                response = f"I can see the following objects in the current view: {object_list}. {question}"
            else:
                response = f"No objects detected in the current view. {question}"
        else:
            response = f"No recent detections available. {question}"

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
