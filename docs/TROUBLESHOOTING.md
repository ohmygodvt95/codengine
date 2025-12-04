# Quick Troubleshooting Guide

## Common Issues and Solutions

### 🔴 Issue: Bubblewrap Not Found

**Error Message:**
```
Failed to execute sandboxed process: [Errno 2] No such file or directory: 'bwrap'
```

**Cause:** Bubblewrap is not installed on the system.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y bubblewrap

# Fedora
sudo dnf install bubblewrap

# Verify
which bwrap
bwrap --version
```

---

### 🔴 Issue: Import Errors

**Error Message:**
```
ImportError: attempted relative import with no known parent package
# or
ModuleNotFoundError: No module named 'app'
```

**Cause:** Python can't find the app module.

**Solution:**
```bash
# Make sure you're in the project root directory
cd /home/ohmygodvt95/codengine

# Check directory structure
ls -la app/

# Reinstall if needed
pip install -r requirements.txt
```

---

### 🔴 Issue: Runtime Not Found

**Error Message:**
```
Runtime for python version 3.11 not found
```

**Cause:** The requested Python version is not installed in `/packages/python/`.

**Solution:**
```bash
# Check installed runtimes
ls -la /packages/python/

# Use an available version, or install the required version
# See docs/INSTALLATION.md for runtime installation guide
```

---

### 🔴 Issue: Port Already in Use

**Error Message:**
```
[Errno 98] Address already in use
```

**Cause:** Port 8000 is already being used by another process.

**Solution:**
```bash
# Option 1: Find and kill the process
sudo lsof -i :8000
sudo kill -9 <PID>

# Option 2: Use a different port
uvicorn main:app --port 8001
```

---

### 🔴 Issue: Permission Denied

**Error Message:**
```
Permission denied when accessing /packages/
```

**Cause:** Insufficient permissions for runtime directories.

**Solution:**
```bash
# Fix permissions
sudo chmod -R 755 /packages/

# Or run with sudo (not recommended for production)
sudo uvicorn main:app
```

---

### 🔴 Issue: Server Crashes on Startup

**Error Message:**
```
Failed to load application
```

**Cause:** Syntax error or missing dependencies.

**Solution:**
```bash
# Test import
python -c "from app import app; print('OK')"

# Check for errors
python -m py_compile app/main.py

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

### 🔴 Issue: Timeout During Execution

**Error Message:**
```
TIMEOUT: Execution exceeded time limit
```

**Cause:** Code takes longer than the specified time limit.

**Solution:**
```bash
# Increase time_limit in your request
{
  "time_limit": 5.0,  // Increase from default 2.0
  ...
}

# Or modify default in .env
DEFAULT_TIME_LIMIT=5.0
```

---

### 🔴 Issue: Memory Limit Exceeded

**Error Message:**
```
Process killed (memory limit)
```

**Cause:** Code uses more memory than allowed.

**Solution:**
```bash
# Increase memory_limit in your request
{
  "memory_limit": 512,  // Increase from default 256
  ...
}

# Or modify default in .env
DEFAULT_MEMORY_LIMIT=512
```

---

### 🔴 Issue: Network Access Blocked

**Symptom:** Code can't access internet even when needed.

**Cause:** Internet is disabled by default for security.

**Solution:**
```bash
# Enable internet in your request
{
  "internet": true,  // Enable network access
  ...
}
```

---

### 🔴 Issue: File Not Found in Execution

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'file.py'
```

**Cause:** Referenced file not included in files array.

**Solution:**
```json
{
  "files": [
    {
      "name": "main.py",
      "content": "from utils import helper"
    },
    {
      "name": "utils.py",  // Make sure to include all files
      "content": "def helper(): pass"
    }
  ]
}
```

---

## Health Check Diagnostics

### Check System Health

```bash
# 1. Check bubblewrap
which bwrap && echo "✅ Bubblewrap installed" || echo "❌ Bubblewrap missing"

# 2. Check Python
python3 --version

# 3. Check virtual environment
which python | grep .venv && echo "✅ In venv" || echo "❌ Not in venv"

# 4. Check dependencies
pip list | grep -E "fastapi|pydantic|uvicorn"

# 5. Check runtimes
ls -la /packages/python/ 2>/dev/null && echo "✅ Runtimes found" || echo "❌ No runtimes"

# 6. Check server
curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null && echo "✅ Server running" || echo "❌ Server not running"
```

### Quick Fix Script

```bash
#!/bin/bash
# quick-fix.sh - Run this to fix common issues

echo "🔧 Running quick fixes..."

# 1. Check and install bubblewrap
if ! which bwrap > /dev/null; then
    echo "Installing bubblewrap..."
    sudo apt-get update && sudo apt-get install -y bubblewrap
fi

# 2. Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate and install dependencies
source .venv/bin/activate
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Check permissions
if [ -d "/packages" ]; then
    echo "Fixing /packages permissions..."
    sudo chmod -R 755 /packages/
fi

echo "✅ Quick fixes completed!"
echo "Try starting the server: uvicorn main:app --reload"
```

---

## Getting Help

If issues persist:

1. **Check logs:** Look at server output for detailed error messages
2. **Check documentation:** See `docs/` for detailed guides
3. **Verify structure:** Run `tree -L 2 app/` to check file organization
4. **Test imports:** Run `python -c "from app import app"`
5. **Check health:** Visit `http://localhost:8000/health`

## Debug Mode

Enable debug mode for more verbose output:

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart server
uvicorn main:app --reload --log-level debug
```

---

**Last Updated:** December 5, 2025
