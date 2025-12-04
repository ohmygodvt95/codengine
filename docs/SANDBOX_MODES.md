# Sandbox Modes - Direct vs Bubblewrap

## Overview

Code Execution Engine hỗ trợ 2 chế độ thực thi:

1. **Sandboxed Mode (Bubblewrap)** - Secure, isolated ✅ Recommended
2. **Direct Mode** - Fallback khi bubblewrap không khả dụng ⚠️ Less secure

## Execution Modes

### 🔒 Sandboxed Mode (Bubblewrap)

**Features:**
- ✅ Full filesystem isolation
- ✅ Network isolation
- ✅ Process isolation  
- ✅ Resource limits (CPU, memory)
- ✅ Read-only runtime packages
- ✅ **Most secure**

**Requirements:**
- Bubblewrap installed
- User namespace support in kernel
- Not running in restrictive environment (WSL1, some containers)

**Auto-detection:**
Engine automatically checks if bubblewrap can create namespaces.

---

### ⚠️ Direct Mode

**Features:**
- ⚠️ No filesystem isolation
- ⚠️ No network isolation
- ⚠️ Limited process isolation
- ✅ Resource limits (CPU, memory) still work
- ⚠️ **Less secure**

**When Used:**
- Bubblewrap not installed
- Bubblewrap can't create namespaces (WSL, containers, kernel restrictions)
- Manually disabled via config

**Security:**
Still applies resource limits (CPU time, memory, process count) but lacks full isolation.

---

## Error: "Creating new namespace failed"

### Symptom
```
bwrap: Creating new namespace failed: Resource temporarily unavailable
```

### Cause
Bubblewrap can't create user namespaces. Common in:
- **WSL (Windows Subsystem for Linux)** - Limited namespace support
- **Docker containers** - May need `--privileged` or `--cap-add=SYS_ADMIN`
- **LXC/LXD containers** - Nested namespaces might be restricted
- **Some cloud VPS** - Kernel compiled without user namespace support

### Solution

Engine automatically falls back to Direct Mode. No action needed!

#### Verify Fallback

Check health endpoint:
```bash
curl http://localhost:8000/health
```

**Sandboxed mode:**
```json
{
  "status": "healthy",
  "execution_mode": "sandboxed (bubblewrap)",
  "bubblewrap_installed": true,
  "bubblewrap_working": true
}
```

**Direct mode (automatic fallback):**
```json
{
  "status": "degraded",
  "execution_mode": "direct (bubblewrap installed but not working)",
  "bubblewrap_installed": true,
  "bubblewrap_working": false
}
```

---

## Manual Configuration

### Force Direct Mode

If you want to disable bubblewrap even when available:

**Option 1: Environment Variable**
```bash
# .env
USE_BUBBLEWRAP=false
```

**Option 2: Config File**
```python
# app/config.py
use_bubblewrap: bool = False
```

**Option 3: Runtime**
```bash
USE_BUBBLEWRAP=false uvicorn main:app
```

### Enable Bubblewrap in Docker

If running in Docker and want bubblewrap:

```dockerfile
FROM python:3.11

# Install bubblewrap
RUN apt-get update && apt-get install -y bubblewrap

# Run with required capabilities
# docker run --cap-add=SYS_ADMIN ...
```

Or in docker-compose:
```yaml
services:
  codengine:
    cap_add:
      - SYS_ADMIN
    # or
    privileged: true  # Less secure but enables namespaces
```

---

## Security Comparison

| Feature | Sandboxed Mode | Direct Mode |
|---------|----------------|-------------|
| Filesystem isolation | ✅ Full | ❌ None |
| Network isolation | ✅ Optional | ❌ None |
| Process isolation | ✅ Full | ⚠️ Limited |
| CPU limit | ✅ Yes | ✅ Yes |
| Memory limit | ✅ Yes | ✅ Yes |
| Process limit | ✅ Yes | ✅ Yes |
| Read-only runtime | ✅ Yes | ❌ No |
| **Security Level** | **High** | **Medium** |

---

## Recommendations

### Production

**Preferred:** Sandboxed Mode
- Run on bare metal or VM with full kernel support
- Avoid WSL, use native Linux
- Enable user namespaces in kernel

**If Direct Mode Required:**
- Additional firewall rules
- Run in isolated network
- Monitor resource usage closely
- Implement rate limiting
- Use application-level sandboxing

### Development

**Either mode acceptable:**
- Direct mode fine for local testing
- Sandboxed mode for production-like environment

### WSL Users

**Direct mode only:**
- WSL1: No namespace support
- WSL2: Limited namespace support
- Engine auto-detects and uses Direct mode
- Consider using Docker Desktop with proper caps

---

## Checking Your Environment

### Test Bubblewrap
```bash
# Check if installed
which bwrap

# Test basic operation
bwrap --ro-bind / / -- echo "test"

# If you see "Creating new namespace failed" → Direct mode will be used
```

### Check Kernel Support
```bash
# Check if user namespaces enabled
cat /proc/sys/user/max_user_namespaces
# Should be > 0

# Check if unprivileged user namespaces allowed (Debian/Ubuntu)
cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null
# Should be 1 (file may not exist on all systems)
```

### Engine Self-Check
```bash
# Start server
uvicorn main:app

# Check health
curl http://localhost:8000/health | python -m json.tool
```

---

## Troubleshooting

### Bubblewrap Installed But Not Working

**Check kernel support:**
```bash
unshare --user --pid --net echo "Namespaces work"
# If fails → Direct mode will be used
```

**WSL-specific:**
```bash
# Check WSL version
wsl --list --verbose

# WSL1 → No namespace support
# WSL2 → Limited support, might need kernel update
```

**Docker-specific:**
```bash
# Run with capability
docker run --cap-add=SYS_ADMIN your-image

# Or check if privileged needed
docker run --privileged your-image
```

### Still Getting Namespace Errors

Engine should auto-fallback. If not:
1. Check logs for "direct mode" message
2. Manually set `USE_BUBBLEWRAP=false`
3. Restart server
4. Verify with `/health` endpoint

---

## Migration Guide

### From Sandboxed to Direct

No code changes needed! Engine auto-detects.

### From Direct to Sandboxed

1. Install bubblewrap: `sudo apt-get install bubblewrap`
2. Enable user namespaces (if needed)
3. Restart server
4. Verify: `curl http://localhost:8000/health`

---

## FAQ

**Q: Is Direct mode safe for production?**
A: Less safe than Sandboxed, but still has resource limits. Use only if Sandboxed not possible.

**Q: Can I switch modes without restart?**
A: No, mode is detected at startup and cached.

**Q: Will my API calls work in both modes?**
A: Yes! API interface is identical.

**Q: Performance difference?**
A: Sandboxed slightly slower (namespace overhead ~10-20ms). Direct mode is faster.

**Q: Can I force Sandboxed mode?**
A: Engine uses Sandboxed if available. You can only force Direct mode.

---

**Last Updated:** December 5, 2025
