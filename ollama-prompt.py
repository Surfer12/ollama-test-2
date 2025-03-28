from flask import Flask, request, jsonify
import ollama
import logging
import os
from dotenv import load_dotenv
from marshmallow import Schema, fields, validate

load_dotenv()
API_KEY = os.getenv('API_KEY')

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

class ChatSchema(Schema):
    messages = fields.List(fields.Dict(keys=fields.Str(), values=fields.Str()), required=True)
    system = fields.Str(required=True)
    tools = fields.List(fields.Str(), required=True)

chat_schema = ChatSchema()

@app.route('/api/v1/chat', methods=['POST'])
def chat():
    logger.info("Received request at /api/v1/chat")
    try:
        data = request.json

        # Validate input data
        errors = chat_schema.validate(data)
        if errors:
            logger.error(f"Validation errors: {errors}")
            return jsonify({"error": "Invalid input data format", "details": errors}), 400

        messages = data.get('messages', [])
        system = data.get('system', "")
        tools = data.get('tools', [])

        # Construct the prompt using the provided messages, system, and tools
        prompt = construct_prompt(messages, system, tools)

        # Use the ollama client to get a response
        response = ollama.get_response(prompt)

        return jsonify(response)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

def construct_prompt(messages, system, tools):
    # Simplified prompt construction
    prompt = f"{system}\n"
    for message in messages:
        prompt += f"{message['role']}: {message['content']}\n"
    prompt += f"Tools available: {', '.join(tools)}"
    return prompt

if __name__ == '__main__':
    app.run(debug=True)
