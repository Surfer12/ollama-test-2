from flask import Flask, request, jsonify, Response
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
    # Model parameters
    temperature = fields.Float(required=False, validate=validate.Range(min=0, max=2), default=0.7)
    max_tokens = fields.Integer(required=False, validate=validate.Range(min=1), default=1000)
    top_p = fields.Float(required=False, validate=validate.Range(min=0, max=1), default=0.9)
    stream = fields.Boolean(required=False, default=False)
    conversation_id = fields.Str(required=False)

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

        # Extract parameters
        messages = data.get('messages', [])
        system = data.get('system', "")
        tools = data.get('tools', [])
        model = data.get('model', "llama2")
        provider = data.get('provider', "ollama")
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        top_p = data.get('top_p', 0.9)
        stream = data.get('stream', False)
        conversation_id = data.get('conversation_id')

        # Log the request details
        logger.info(f"Processing request with provider: {provider}, model: {model}, stream: {stream}")
        
        # Save conversation history if conversation_id is provided
        if conversation_id:
            save_conversation_history(conversation_id, messages)
        
        # Handle streaming response
        if stream:
            def generate():
                try:
                    # Route to the appropriate provider for streaming
                    if provider == "ollama":
                        for chunk in process_ollama_stream(messages, system, tools, model, temperature, max_tokens, top_p):
                            yield f"data: {json.dumps(chunk)}\n\n"
                    elif provider == "openai":
                        for chunk in process_openai_stream(messages, system, tools, model, temperature, max_tokens, top_p):
                            yield f"data: {json.dumps(chunk)}\n\n"
                    elif provider == "anthropic":
                        for chunk in process_anthropic_stream(messages, system, tools, model, temperature, max_tokens, top_p):
                            yield f"data: {json.dumps(chunk)}\n\n"
                    elif provider == "mistral":
                        for chunk in process_mistral_stream(messages, system, tools, model, temperature, max_tokens, top_p):
                            yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        yield f"data: {json.dumps({'error': 'Invalid provider specified'})}\n\n"
                        
                    # End of stream marker
                    yield f"data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(generate(), mimetype='text/event-stream')
            
        else:
            # Non-streaming response
            # Route to the appropriate provider
            if provider == "ollama":
                response = process_ollama_request(messages, system, tools, model, temperature, max_tokens, top_p)
            elif provider == "openai":
                response = process_openai_request(messages, system, tools, model, temperature, max_tokens, top_p)
            elif provider == "anthropic":
                response = process_anthropic_request(messages, system, tools, model, temperature, max_tokens, top_p)
            elif provider == "mistral":
                response = process_mistral_request(messages, system, tools, model, temperature, max_tokens, top_p)
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

# Conversation history storage
conversation_histories = {}

def save_conversation_history(conversation_id, messages):
    """Store conversation history in memory"""
    conversation_histories[conversation_id] = messages
    # Trim history if it gets too large (limit to last 20 messages)
    if len(conversation_histories[conversation_id]) > 20:
        conversation_histories[conversation_id] = conversation_histories[conversation_id][-20:]

def get_conversation_history(conversation_id):
    """Retrieve conversation history"""
    return conversation_histories.get(conversation_id, [])

def process_ollama_request(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Process a request to the Ollama API"""
    # Use the ollama client to get a response
    response = ollama.chat(
        model=model, 
        messages=[
            {"role": "system", "content": system},
            *[{"role": m["role"], "content": m["content"]} for m in messages]
        ],
        options={
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens
        }
    )
    
    return response

def process_ollama_stream(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Stream a response from the Ollama API"""
    for chunk in ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            *[{"role": m["role"], "content": m["content"]} for m in messages]
        ],
        options={
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens
        },
        stream=True
    ):
        yield chunk

def process_openai_request(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Process a request to the OpenAI API"""
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
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p
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

def process_openai_stream(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Stream a response from the OpenAI API"""
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
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "stream": True
    }
    
    if tools and len(tools) > 0:
        payload["tools"] = [{"type": "function", "function": {"name": tool}} for tool in tools]
    
    response = requests.post("https://api.openai.com/v1/chat/completions", 
                           headers=headers, 
                           json=payload,
                           stream=True)
    
    if response.status_code != 200:
        raise Exception(f"OpenAI API error: {response.status_code}")
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                if line.startswith('data: [DONE]'):
                    break
                data = json.loads(line[6:])
                yield data

def process_anthropic_request(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Process a request to the Anthropic API"""
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
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
    
    response = requests.post("https://api.anthropic.com/v1/messages", 
                           headers=headers, 
                           json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Anthropic API error: {response.text}")
    
    return response.json()

def process_anthropic_stream(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Stream a response from the Anthropic API"""
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
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": True
    }
    
    response = requests.post("https://api.anthropic.com/v1/messages", 
                           headers=headers, 
                           json=payload,
                           stream=True)
    
    if response.status_code != 200:
        raise Exception(f"Anthropic API error: {response.status_code}")
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('event: content_block_delta'):
                # Skip to the actual data
                continue
            if line.startswith('data: '):
                if line.startswith('data: [DONE]'):
                    break
                data = json.loads(line[6:])
                yield data

def process_mistral_request(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Process a request to the Mistral API"""
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
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p
    }
    
    response = requests.post("https://api.mistral.ai/v1/chat/completions", 
                           headers=headers, 
                           json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Mistral API error: {response.text}")
    
    return response.json()

def process_mistral_stream(messages, system, tools, model, temperature=0.7, max_tokens=1000, top_p=0.9):
    """Stream a response from the Mistral API"""
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
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "stream": True
    }
    
    response = requests.post("https://api.mistral.ai/v1/chat/completions", 
                           headers=headers, 
                           json=payload,
                           stream=True)
    
    if response.status_code != 200:
        raise Exception(f"Mistral API error: {response.status_code}")
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                if line.startswith('data: [DONE]'):
                    break
                data = json.loads(line[6:])
                yield data

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0",
        "providers": {
            "ollama": OLLAMA_API_KEY is not None,
            "openai": OPENAI_API_KEY is not None,
            "anthropic": ANTHROPIC_API_KEY is not None,
            "mistral": MISTRAL_API_KEY is not None
        }
    })

@app.route('/api/v1/models', methods=['GET'])
def list_models():
    """List available models for each provider"""
    provider = request.args.get('provider')
    models = {}
    
    try:
        # Ollama models
        if not provider or provider == 'ollama':
            try:
                ollama_models = ollama.list()
                models['ollama'] = [model['name'] for model in ollama_models.get('models', [])]
            except Exception as e:
                logger.warning(f"Error fetching Ollama models: {e}")
                models['ollama'] = []
        
        # OpenAI models
        if (not provider or provider == 'openai') and OPENAI_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                }
                response = requests.get("https://api.openai.com/v1/models", headers=headers)
                if response.status_code == 200:
                    openai_models = response.json()
                    # Filter for only chat models
                    chat_models = [model['id'] for model in openai_models.get('data', []) 
                                if model['id'].startswith(('gpt-', 'text-davinci-'))]
                    models['openai'] = chat_models
                else:
                    models['openai'] = []
            except Exception as e:
                logger.warning(f"Error fetching OpenAI models: {e}")
                models['openai'] = []
        
        # Anthropic models (hardcoded since API doesn't provide a models endpoint)
        if (not provider or provider == 'anthropic') and ANTHROPIC_API_KEY:
            models['anthropic'] = [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0",
                "claude-instant-1.2"
            ]
        
        # Mistral models (hardcoded as API doesn't have a public models endpoint)
        if (not provider or provider == 'mistral') and MISTRAL_API_KEY:
            models['mistral'] = [
                "mistral-tiny",
                "mistral-small",
                "mistral-medium",
                "mistral-large-latest"
            ]
        
        return jsonify({"models": models})
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/embeddings', methods=['POST'])
def generate_embeddings():
    """Generate embeddings for text"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = data.get('text')
        provider = data.get('provider', 'openai')
        model = data.get('model')
        
        if provider == 'openai':
            if not OPENAI_API_KEY:
                return jsonify({"error": "OpenAI API key not configured"}), 500
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
            
            payload = {
                "input": text,
                "model": model or "text-embedding-ada-002"
            }
            
            response = requests.post("https://api.openai.com/v1/embeddings", 
                                   headers=headers, 
                                   json=payload)
            
            if response.status_code != 200:
                return jsonify({"error": f"OpenAI API error: {response.text}"}), response.status_code
            
            return jsonify(response.json())
            
        elif provider == 'ollama':
            # Use Ollama for embeddings
            response = ollama.embeddings(model=model or "llama2", prompt=text)
            return jsonify(response)
            
        else:
            return jsonify({"error": "Unsupported provider for embeddings"}), 400
            
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Retrieve conversation history"""
    try:
        history = get_conversation_history(conversation_id)
        return jsonify({"conversation_id": conversation_id, "messages": history})
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete conversation history"""
    try:
        if conversation_id in conversation_histories:
            del conversation_histories[conversation_id]
            return jsonify({"status": "deleted", "conversation_id": conversation_id})
        else:
            return jsonify({"error": "Conversation not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    ssl_context = None
    
    # Check if SSL certificates exist
    cert_path = os.getenv('SSL_CERT_PATH')
    key_path = os.getenv('SSL_KEY_PATH')
    
    if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = (cert_path, key_path)
        logger.info(f"HTTPS enabled with certificates: {cert_path}, {key_path}")
    else:
        logger.warning("HTTPS certificates not found or not configured, running without HTTPS")
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"Starting server on {host}:{port} with HTTPS: {ssl_context is not None}")
    
    app.run(
        debug=os.getenv('DEBUG', 'False').lower() in ('true', '1', 't'),
        host=host,
        port=port,
        ssl_context=ssl_context
    )
