# Copilot Instructions - Code Execution Engine

## Architecture Overview

This is a **secure code execution engine** similar to Piston, built with FastAPI. The core concept: execute untrusted user code safely using **bubblewrap sandboxing** with resource limits.

### Three-Layer Architecture

```
API Layer (app/api/routes.py)
  ↓ orchestrates
Core Layer (app/core/executor.py → runtime.py → sandbox.py)
  ↓ uses
Models (app/models/schemas.py) + Config (app/config.py)
```

- **API Layer**: HTTP request handling, validation, error translation
- **Core Layer**: Business logic for execution, runtime discovery, sandboxing
- **Models Layer**: Pydantic schemas with validation rules

### Critical Design Decisions

**Dual-Mode Execution**: The engine automatically detects sandbox availability and falls back gracefully:
- `SandboxManager.check_bubblewrap_working()` tests if bubblewrap can create namespaces (not just if it's installed)
- Sandboxed mode (bubblewrap): Full filesystem/network/process isolation
- Direct mode (fallback): Resource limits only via `preexec_fn` - used in WSL, containers, or when bwrap unavailable

**Runtime Management**: Runtimes stored in `/packages/{language}/{version}/bin/` structure. Version matching uses prefix-based fallback (e.g., "3.11" finds "3.11.9"). See `RuntimeManager.find_version_dir()`.

**Resource Control**: Applied via `resource.setrlimit()` in `create_resource_limiter()` - works in both modes. Bubblewrap adds filesystem/network isolation on top.

## Development Workflow

### Running the Server

```bash
# Preferred method (uses settings from config)
uvicorn main:app --reload

# Direct python (uses app.config.settings for host/port)
python main.py

# The entry point is main.py which imports from app/__init__.py
```

### Testing

Use `tests/test_api.py` - it's a **requests-based integration test suite**, not pytest. Run directly:
```bash
python tests/test_api.py
```

Test against live server at configured port (check `BASE_URL` in test file).

### Adding New Languages

1. Add language config to `RuntimeManager.SUPPORTED_LANGUAGES` dict in `app/core/runtime.py`
2. Install runtime to `/packages/{language}/{version}/bin/` directory structure
3. Update validator in `ExecRequest.validate_language()` in `app/models/schemas.py`
4. No changes needed in executor or sandbox layers (they're language-agnostic)

## Code Conventions

### Import Pattern

Always use package-relative imports for internal modules:
```python
from app.models import ExecRequest, ExecResult  # ✓ Correct
from app.core import CodeExecutor              # ✓ Correct
from models.schemas import ExecRequest         # ✗ Wrong
```

The `app/` package exports components via `__init__.py` files. See `app/__init__.py` for the public API.

### Error Handling Hierarchy

Custom exceptions inherit from `CodeEngineException` (see `app/exceptions.py`):
- `RuntimeNotFoundException` - Language/version not found
- `UnsupportedLanguageException` - Language not supported
- `SandboxExecutionException` - Execution failures
- `FileSystemException` - Workspace preparation errors

**Pattern**: Core layer raises specific exceptions → API layer catches and converts to HTTP responses via exception handler in `app/main.py`.

### Configuration

All limits defined in `app/config.py` using pydantic-settings:
- Resource limits: `max_time_limit`, `max_memory_limit`
- Output limits: `max_output_size`, `max_stderr_size` (enforced in `CodeExecutor.truncate_output()`)
- File limits: `max_file_size`, `max_files_count` (validated in Pydantic models)

Override via environment variables or `.env` file.

## Critical Code Patterns

### Execution Flow (app/core/executor.py)

1. `execute_code()` creates temp workspace with `tempfile.TemporaryDirectory()`
2. `prepare_workspace()` writes all files from request
3. Get runtime command via `RuntimeManager.get_runtime_command()`
4. Check sandbox availability: `sandbox_manager.check_bubblewrap_working()`
5. Build command: `build_bubblewrap_command()` or `build_direct_command()`
6. Execute: `_run_sandboxed_process()` applies resource limits via `preexec_fn`
7. Truncate outputs if needed before returning `ExecResult`

**Important**: First file in `request.files` list is the main executable file.

### Bubblewrap Command Construction (app/core/sandbox.py)

```python
# Pattern: ro-bind system dirs, bind workspace, unshare network, set limits
bwrap --ro-bind /usr /usr --ro-bind /lib /lib 
      --bind {workdir} /app --chdir /app
      --unshare-net  # Only if internet=False
      -- {runtime_cmd}
```

The `--` separator is critical - it separates bwrap options from the command to execute.

### Output Truncation

`truncate_output()` enforces size limits with UTF-8 safety:
- Truncates at byte level but decodes with `errors='ignore'` to avoid broken characters
- Adds warning message to truncated output
- Prevents context overflow from long outputs

## Integration Points

**External Dependencies**:
- Bubblewrap (`bwrap`) - system package, required for sandboxing
- Runtime packages - reuses Piston packages structure (see `packages/README.md`)

**FastAPI Integration**:
- App factory: `create_app()` in `app/main.py` configures CORS, routes, exception handlers
- Router: Single `router` instance in `app/api/routes.py` included in app
- Validation: Happens automatically via Pydantic models before reaching handlers

## Common Pitfalls

1. **Don't assume bubblewrap works** - always check with `check_bubblewrap_working()`, not just `validate_bubblewrap_available()`
2. **Workspace cleanup** - use `tempfile.TemporaryDirectory()` context manager, never manual cleanup
3. **First file is main** - `request.files[0]` is executed, order matters
4. **Resource limits in both modes** - `preexec_fn` works even without bubblewrap
5. **Version matching** - "3.11" matches "3.11.9" via prefix logic in `find_version_dir()`

## Key Files Reference

- `app/core/executor.py` - Main execution orchestration and workspace management
- `app/core/sandbox.py` - Bubblewrap command construction and resource limiting
- `app/core/runtime.py` - Language runtime discovery and command building
- `app/models/schemas.py` - Request/response models with validation
- `app/config.py` - All configurable limits and settings
- `docs/SANDBOX_MODES.md` - Detailed sandbox behavior documentation
