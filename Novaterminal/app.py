from flask import Flask, render_template, request, jsonify
import os

# This is a placeholder for your core logic.
# Ensure you have a core.py file in the same directory.
try:
    from core import handle_message, init_memory
except ImportError:
    print("Warning: core.py not found. Using placeholder functions.")
    def handle_message(msg):
        return f"This is a test response to: {msg} ⚡"
    def init_memory():
        print("Initializing memory (placeholder)...")
        return "NOVA Online. System ready."

# Initialize Flask App
app = Flask(__name__)

# Initialize NOVA's memory once on startup
# This simulates the original app's behavior
initial_message = init_memory()

# --- ROUTES ---

@app.route('/')
def index():
    """Renders the main chat interface page."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint to handle chat messages."""
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({'error': 'No message provided.'}), 400

        # Get response from your core logic
        nova_response = handle_message(user_message)

        return jsonify({'response': nova_response})

    except Exception as e:
        print(f"Error in /api/chat: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500
        
@app.route('/api/init', methods=['GET'])
def get_initial_message():
    """Provides the initial welcome message from NOVA."""
    return jsonify({'response': initial_message})


if __name__ == '__main__':
    # Use '0.0.0.0' to make the app accessible on your local network
    app.run(host='0.0.0.0', port=5000, debug=True)
