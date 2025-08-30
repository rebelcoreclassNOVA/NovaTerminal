from flask import Flask, render_template, request, jsonify
import os

# --- CORE LOGIC INTEGRATION ---
# This section imports your custom logic from the core.py file.
# If core.py is not found, it uses simple placeholder functions
# so the web app can still run for testing purposes.
try:
    from core import handle_message, init_memory
    print("✅ Successfully imported from core.py")
except ImportError:
    print("⚠️  Warning: core.py not found. Using placeholder functions.")
    def handle_message(msg: str) -> str:
        """A placeholder function that echoes the user's message."""
        # In a real scenario, this would involve complex logic.
        return f"Placeholder response to: \"{msg}\" ⚡"

    def init_memory() -> str:
        """A placeholder function for app initialization."""
        print("Initializing with placeholder memory...")
        return "NOVA Online. System ready. (Placeholder)"

# Initialize the Flask Application
app = Flask(__name__)

# --- APPLICATION STARTUP ---
# Initialize NOVA's "memory" once when the server starts.
# The returned message is stored and sent to the first user
# who opens the chat screen.
print("Initializing NOVA Engine...")
initial_message = init_memory()
print("NOVA Engine Initialized.")


# --- WEB ROUTES ---

@app.route('/')
def index():
    """
    Serves the main HTML page of the application.
    This is the entry point for users visiting the site.
    """
    return render_template('index.html')


# --- API ENDPOINTS ---

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to process user chat messages.
    It receives a JSON object with a "message" key, passes it to the
    core logic, and returns NOVA's response.
    """
    try:
        # Extract the JSON data sent from the frontend JavaScript
        data = request.get_json()
        user_message = data.get('message')

        # Basic validation
        if not user_message:
            return jsonify({'error': 'No message provided.'}), 400

        # Call the main logic function from core.py
        nova_response = handle_message(user_message)

        # Return the response in JSON format
        return jsonify({'response': nova_response})

    except Exception as e:
        # Log the error for debugging and return a generic server error
        print(f"Error in /api/chat endpoint: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/init', methods=['GET'])
def get_initial_message():
    """
    Provides the initial welcome message from NOVA when the chat screen
    is first loaded by the user.
    """
    return jsonify({'response': initial_message})


# --- MAIN EXECUTION BLOCK ---

if __name__ == '__main__':
    """
    This block runs the Flask application when the script is executed directly.
    - host='0.0.0.0' makes the server accessible on your local network.
    - port=5000 is the standard port for Flask development.
    - debug=True enables auto-reloading when you save changes to the code.
    """
    # Note: For a production deployment, you would use a proper WSGI server
    # like Gunicorn or Waitress instead of Flask's built-in development server.
    app.run(host='0.0.0.0', port=5000, debug=True)
