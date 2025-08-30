from flask import Flask, request, jsonify
import os
import random

# --- CONFIG ---
# Seeding for any random operations you might need
random.seed(os.urandom(16))

# This is the placeholder for your core logic.
# For this to work on a server, make sure your 'core.py' file
# is in the same directory as this 'app.py' file.
try:
    from core import handle_message, init_memory, display_help
    print("✅ Successfully imported functions from core.py")
except ImportError:
    print("⚠️ Could not import from core.py. Using placeholder functions.")
    def handle_message(msg):
        """Processes the user's message and returns a response."""
        return f"This is a test response to: {msg} ⚡"

    def init_memory():
        """Initializes the application's memory or state."""
        print("Initializing memory...")
        # In a real app, this might load models, data, etc.
        return "Memory initialized successfully."

    def display_help():
        """Returns a help message."""
        return "Help: Use /chat?message=... to talk to NOVA. Use /init to reset memory."

# --- FLASK APP SETUP ---
app = Flask(__name__)

# --- API ROUTES (ENDPOINTS) ---

@app.route('/')
def index():
    """
    Root endpoint to provide basic API usage instructions.
    Access this by going to your app's main URL.
    """
    return jsonify({
        "message": "Welcome to the NOVA Paralogic Engine API.",
        "usage": {
            "/chat": "Send a message to NOVA. Usage: /chat?message=YourMessageHere",
            "/init": "Re-initialize the system memory.",
            "/help": "Display the help message."
        }
    })

@app.route('/run') # Added /run as requested, which will function like /chat
@app.route('/chat')
def run_chat():
    """
    Handles chat messages. Expects a 'message' query parameter.
    Example: http://127.0.0.1:5000/chat?message=hello
    """
    user_message = request.args.get('message')

    if not user_message:
        return jsonify({"error": "A 'message' query parameter is required."}), 400

    try:
        # Call your core logic function to get a response
        nova_response = handle_message(user_message)
        return jsonify({
            "user_message": user_message,
            "nova_response": nova_response
        })
    except Exception as e:
        # Return a structured error if the core logic fails
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/init')
def initialize_system():
    """
    Triggers the memory initialization function.
    """
    try:
        result = init_memory()
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return jsonify({"error": f"Initialization failed: {str(e)}"}), 500

@app.route('/help')
def get_help():
    """
    Returns the help text from the core logic.
    """
    try:
        help_text = display_help()
        return jsonify({"help_text": help_text})
    except Exception as e:
        return jsonify({"error": f"Could not retrieve help: {str(e)}"}), 500

# --- RUN THE SERVER ---
if __name__ == '__main__':
    # Initialize the memory once when the server starts
    init_memory()
    
    # Hosting providers like Render use the PORT environment variable.
    # We default to 5000 for local testing.
    port = int(os.environ.get('PORT', 5000))
    
    # '0.0.0.0' makes the server accessible from outside its container,
    # which is required by hosting platforms. For local testing, you can
    # access it at http://127.0.0.1:5000 or http://localhost:5000
    app.run(host='0.0.0.0', port=port)
