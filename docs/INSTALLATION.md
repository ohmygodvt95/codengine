# Installation Guide

## System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian, Fedora, etc.)
- **Python**: 3.10 or higher
- **Bubblewrap**: For sandboxing (required)

## Step-by-Step Installation

### 1. Install Bubblewrap

Bubblewrap is **required** for secure code execution sandboxing.

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y bubblewrap
```

#### Fedora
```bash
sudo dnf install bubblewrap
```

#### Arch Linux
```bash
sudo pacman -S bubblewrap
```

#### Verify Installation
```bash

which bwrap
# Should output: /usr/bin/bwrap

sudo chmod u+s /usr/bin/bwrap

bwrap --version
# Should output: bubblewrap 0.x.x
```

#### Test Bubblewrap
```bash
bwrap --ro-bind / / --dev /dev --proc /proc -- echo "Test successful!"
# Should output: Test successful!
```

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd codengine
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit configuration if needed
nano .env
```

### 6. Install Language Runtimes

The engine needs runtime interpreters installed in `/packages/` directory.

#### Install Python Runtime

```bash
# Example: Install Python 3.11
sudo mkdir -p /packages/python
cd /tmp

# Download Python
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xzf Python-3.11.9.tgz
cd Python-3.11.9

# Configure and build
./configure --prefix=/packages/python/3.11.9 --enable-optimizations
make -j$(nproc)
sudo make install

# Verify
/packages/python/3.11.9/bin/python3 --version
```

#### Install Node.js Runtime (Optional)

```bash
# Example: Install Node.js 18
sudo mkdir -p /packages/node
cd /tmp

# Download Node.js
wget https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.xz
tar -xJf node-v18.19.0-linux-x64.tar.xz
sudo mv node-v18.19.0-linux-x64 /packages/node/18.19.0

# Verify
/packages/node/18.19.0/bin/node --version
```

### 7. Test Installation

```bash
# Start server
uvicorn main:app --reload

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "bubblewrap": "available"
# }
```

## Troubleshooting

### Bubblewrap Not Found

**Error:** `Failed to execute sandboxed process: [Errno 2] No such file or directory: 'bwrap'`

**Solution:**
```bash
# Install bubblewrap
sudo apt-get install -y bubblewrap

# Verify
which bwrap
```

### Permission Denied

**Error:** `Permission denied` when running bubblewrap

**Solution:**
```bash
# Check if bubblewrap has correct permissions
ls -la $(which bwrap)

# Should have setuid bit: -rwsr-xr-x
# If not, reinstall bubblewrap
sudo apt-get install --reinstall bubblewrap
```

### Runtime Not Found

**Error:** `Runtime version 'X.Y.Z' not found`

**Solution:**
```bash
# Check installed runtimes
ls -la /packages/python/
ls -la /packages/node/

# Install required runtime (see step 6)
```

### Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Make sure you're in project root
pwd  # Should be: /path/to/codengine

# Check if app/ directory exists
ls -la app/

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

**Error:** `[Errno 98] Address already in use`

**Solution:**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

## Verification Checklist

After installation, verify everything is working:

- [ ] Bubblewrap is installed: `which bwrap` returns a path
- [ ] Python dependencies installed: `pip list` shows fastapi, pydantic, uvicorn
- [ ] At least one runtime installed: `ls /packages/python/` shows versions
- [ ] Server starts: `uvicorn main:app` runs without errors
- [ ] Health check passes: `curl http://localhost:8000/health` returns healthy status
- [ ] Execute endpoint works: Test with a simple Python script

## Quick Start After Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Start server
uvicorn main:app --reload

# Or use the startup script
./scripts/start.sh
```

Server will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Next Steps

- Read [API Documentation](README.md)
- Check [Architecture Guide](ARCHITECTURE.md)
- View [Usage Examples](../scripts/examples.py)
- Run [Tests](../tests/test_api.py)
