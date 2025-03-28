# Ollama Project Guidelines

## Commands
- Setup: `pip install -r requirements.txt`
- Run: `python ollama-prompt.py`
- Lint: `flake8 *.py`
- Format: `black *.py`
- Test: `pytest`
- Single test: `pytest tests/test_file.py::test_function -v`

## Environment Variables
- `OLLAMA_API_KEY`: API key for Ollama (if required)
- `OPENAI_API_KEY`: API key for OpenAI services
- `ANTHROPIC_API_KEY`: API key for Anthropic services
- `MISTRAL_API_KEY`: API key for Mistral services

## Server Configuration
- `HOST`: Host address to bind to (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 5000)
- `DEBUG`: Enable debug mode (default: False)
- `SSL_CERT_PATH`: Path to SSL certificate for HTTPS
- `SSL_KEY_PATH`: Path to SSL private key for HTTPS

## Code Style Guidelines
- **Formatting**: Use Black with default settings
- **Imports**: Group standard library, third-party, then local imports
- **Typing**: Use type hints for function parameters and return values
- **Naming**:
  - Classes: PascalCase
  - Functions/variables: snake_case
  - Constants: UPPER_SNAKE_CASE
- **Error Handling**: Use try/except with specific exceptions
- **Logging**: Use Python's logging module, not print statements
- **Documentation**: Docstrings for all functions and classes (Google style)
- **API Endpoints**: RESTful design with proper error responses
- **Security**: Never hardcode credentials; use environment variables