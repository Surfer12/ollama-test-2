from flask import Flask, request, jsonify
import ollama
import logging
import os
from dotenv import load_dotenv
from marshmallow import Schema, fields, validate
import requests
import json
from logging.handlers import RotatingFileHandler

load_dotenv()
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

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
    tools = fields.List(fields.Str(), required=False)
    model = fields.Str(required=False, default="llama2")
    provider = fields.Str(required=False, default="ollama", 
                         validate=validate.OneOf(["ollama", "openai", "anthropic", "mistral"]))

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
        model = data.get('model', "llama2")
        provider = data.get('provider', "ollama")

        logger.info(f"Processing request with provider: {provider}, model: {model}")
        
        # Route to the appropriate provider
        if provider == "ollama":
            response = process_ollama_request(messages, system, tools, model)
        elif provider == "openai":
            response = process_openai_request(messages, system, tools, model)
        elif provider == "anthropic":
            response = process_anthropic_request(messages, system, tools, model)
        elif provider == "mistral":
            response = process_mistral_request(messages, system, tools, model)
        else:
            return jsonify({"error": "Invalid provider specified"}), 400

        return jsonify(response)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500

def construct_prompt(messages, system, tools):
    # Simplified prompt construction
    prompt = f"{system}\n"
    for message in messages:
        prompt += f"{message['role']}: {message['content']}\n"
    if tools and len(tools) > 0:
        prompt += f"Tools available: {', '.join(tools)}"
    return prompt

def process_ollama_request(messages, system, tools, model):
    # Construct the prompt using the provided messages, system, and tools
    prompt = construct_prompt(messages, system, tools)
    
    # Use the ollama client to get a response
    response = ollama.chat(model=model, messages=[
        {"role": "system", "content": system},
        *[{"role": m["role"], "content": m["content"]} for m in messages]
    ])
    
    return response

def process_openai_request(messages, system, tools, model):
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            *[{"role": m["role"], "content": m["content"]} for m in messages]
        ]
    }
    
    if tools and len(tools) > 0:
        # Format tools for OpenAI - simplistic implementation
        payload["tools"] = [{"type": "function", "function": {"name": tool}} for tool in tools]
    
    response = requests.post("https://api.openai.com/v1/chat/completions", 
                           headers=headers, 
                           json=payload)
    
    if response.status_code != 200:
        raise Exception(f"OpenAI API error: {response.text}")
    
    return response.json()

def process_anthropic_request(messages, system, tools, model):
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key not configured")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    # Convert messages to Anthropic format
    anthropic_messages = []
    for message in messages:
        role = "assistant" if message["role"] == "assistant" else "user"
        anthropic_messages.append({"role": role, "content": message["content"]})
    
    payload = {
        "model": model,
        "messages": anthropic_messages,
        "system": system,
        "max_tokens": 1000
    }
    
    response = requests.post("https://api.anthropic.com/v1/messages", 
                           headers=headers, 
                           json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Anthropic API error: {response.text}")
    
    return response.json()

def process_mistral_request(messages, system, tools, model):
    if not MISTRAL_API_KEY:
        raise ValueError("Mistral API key not configured")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            *[{"role": m["role"], "content": m["content"]} for m in messages]
        ]
    }
    
    response = requests.post("https://api.mistral.ai/v1/chat/completions", 
                           headers=headers, 
                           json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Mistral API error: {response.text}")
    
    return response.json()

if __name__ == '__main__':
    app.run(debug=True)
