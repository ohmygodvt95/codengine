# Code Execution Engine

A secure, sandboxed code execution engine similar to Piston, built with FastAPI.

## 📁 Project Structure

```
codengine/
├── app/                      # Main application package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI app creation
│   ├── config.py            # Configuration management
│   ├── exceptions.py        # Custom exceptions
│   │
│   ├── api/                 # API layer
│   │   ├── __init__.py
│   │   └── routes.py        # API route handlers
│   │
│   ├── core/                # Core business logic
│   │   ├── __init__.py
│   │   ├── executor.py      # Code execution engine
│   │   ├── runtime.py       # Runtime management
│   │   └── sandbox.py       # Sandbox environment
│   │
│   └── models/              # Data models
│       ├── __init__.py
│       └── schemas.py       # Pydantic schemas
│
├── tests/                   # Test files
│   ├── __init__.py
│   └── test_api.py          # API tests
│
├── docs/                    # Documentation
│   ├── README.md            # Detailed documentation
│   ├── ARCHITECTURE.md      # Architecture guide
│   ├── GUIDE_VI.md          # Vietnamese guide
│   └── CHANGELOG.md         # Change history
│
├── scripts/                 # Utility scripts
│   ├── start.sh             # Server startup script
│   └── examples.py          # Usage examples
│
├── packages/                # Runtime packages
│   ├── python/              # Python runtimes
│   └── node/                # Node.js runtimes
│
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── .gitignore               # Git ignore rules
```

## 🚀 Quick Start

### Prerequisites

**Bubblewrap** is required for sandboxing:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y bubblewrap

# Fedora
sudo dnf install bubblewrap

# Verify installation
which bwrap
bwrap --version
```

### Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Method 1: Use start script
./scripts/start.sh

# Method 2: Direct uvicorn
uvicorn main:app --reload

# Method 3: Python direct
python main.py
```

Server will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📖 Documentation

Full documentation is available in the `docs/` directory:

- **[README.md](docs/README.md)** - Complete API documentation and usage guide
- **[INSTALLATION.md](docs/INSTALLATION.md)** - Detailed installation instructions
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design patterns
- **[GUIDE_VI.md](docs/GUIDE_VI.md)** - Vietnamese user guide with examples
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history and changes

## 🔑 Key Features

- 🔒 **Secure Sandboxing** - Bubblewrap containerization
- ⚡ **Resource Limits** - CPU time and memory constraints
- 🌐 **Network Control** - Optional internet access
- 🐍 **Multi-Language** - Python and Node.js support
- 📦 **Modular Design** - Clean separation of concerns
- 🛡️ **Error Handling** - Comprehensive error handling

## 📚 API Endpoints

### Execute Code
```http
POST /api/v2/execute
```

### Get Runtimes
```http
GET /api/v2/runtimes
```

### Health Check
```http
GET /health
```

## 🧪 Testing

```bash
# Run test suite
python tests/test_api.py

# Or with pytest (if installed)
pytest tests/
```

## 📝 Example Usage

```python
import requests

response = requests.post("http://localhost:8000/api/v2/execute", json={
    "language": "python",
    "version": "3.11",
    "files": [{
        "name": "main.py",
        "content": "print('Hello, World!')"
    }]
})

print(response.json())
```

More examples available in `scripts/examples.py`

## 🔧 Configuration

Configuration can be set via environment variables or `.env` file.
See `.env.example` for all available options.

## 📄 License

MIT

## 🤝 Contributing

See documentation in `docs/` for architecture and development guidelines.
