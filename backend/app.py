from flask import Flask, request, jsonify, Response
import time

app = Flask(__name__)

# Global variable to store the latest frame
latest_frame = None

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
