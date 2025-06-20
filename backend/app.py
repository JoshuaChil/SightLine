from flask import Flask, request, jsonify
import time

app = Flask(__name__)

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
