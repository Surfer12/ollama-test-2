# Ollama API Documentation

This API provides a unified interface to interact with multiple language model providers through a single consistent interface.

## Available Providers

- `ollama`: Local models powered by Ollama
- `openai`: OpenAI models including GPT-4 and GPT-3.5
- `anthropic`: Anthropic Claude models
- `mistral`: Mistral AI models

## Authentication

API keys for each provider must be set in the `.env` file.

## Chat Completion API

### Endpoint

```
POST /api/v1/chat
```

### Request Body

```json
{
  "provider": "ollama",       // Optional (default: "ollama")
  "model": "nemotron-mini-latest",          // Optional (default depends on provider)
  "messages": [               // Required
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "system": "You are a helpful assistant", // Required
  "tools": ["calculator", "weather"],      // Optional
  "temperature": 0.7,                      // Optional (default: 0.7)
  "max_tokens": 1000,                      // Optional (default: 1000)
  "top_p": 0.9,                            // Optional (default: 0.9)
  "stream": false,                         // Optional (default: false)
  "conversation_id": "abc123"              // Optional
}
```

### Response (Non-streaming)

```json
{
  "id": "response-id",
  "model": "nemotron-mini-latest",
  "created_at": "2023-01-01T00:00:00Z",
  "message": {
    "role": "assistant",
    "content": "I'm doing well, thank you for asking! How can I help you today?"
  }
}
```

### Streaming Response

When `stream: true` is set, the API returns chunked responses using Server-Sent Events (SSE) format:

```
data: {"id": "response-id", "delta": "I'm "}
data: {"id": "response-id", "delta": "doing "}
data: {"id": "response-id", "delta": "well, "}
data: [DONE]
```

## Models API

Lists available models for each configured provider.

### Endpoint

```
GET /api/v1/models
```

### Query Parameters

- `provider`: Optional filter for a specific provider

### Response

```json
{
  "models": {
    "ollama": ["mistral:orca", "phi2"],
    "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
    "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    "mistral": ["mistral-tiny", "mistral-small", "mistral-medium", "mistral-large-latest"]
  }
}
```

## Embeddings API

Generates vector embeddings for input text.

### Endpoint

```
POST /api/v1/embeddings
```

### Request Body

```json
{
  "text": "The quick brown fox jumps over the lazy dog",
  "provider": "openai",  // Optional (default: "openai")
  "model": "text-embedding-ada-002"  // Optional (depends on provider)
}
```

### Response

```json
{
  "embedding": [0.1, 0.2, 0.3, ...],
  "provider": "openai",
  "model": "text-embedding-ada-002",
  "token_count": 10
}
```

## Conversation Management API

Manages conversation history.

### Get Conversation

```
GET /api/v1/conversations/{conversation_id}
```

#### Response

```json
{
  "conversation_id": "abc123",
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hi there! How can I help you today?"
    }
  ]
}
```

### Delete Conversation

```
DELETE /api/v1/conversations/{conversation_id}
```

#### Response

```json
{
  "status": "deleted",
  "conversation_id": "abc123"
}
```

## Health Check API

Returns the status of the API and configured providers.

### Endpoint

```
GET /health
```

### Response

```json
{
  "status": "ok",
  "version": "1.0",
  "providers": {
    "ollama": true,
    "openai": true,
    "anthropic": false,
    "mistral": false
  }
}
```
