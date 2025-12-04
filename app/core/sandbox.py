"""
Sandbox management for secure code execution.
"""
import os
import resource
import subprocess
from typing import List, Callable, Optional
from app.config import settings

class SandboxManager:
    """Manages sandbox environment for code execution."""
    
    _bwrap_available: Optional[bool] = None
    _bwrap_working: Optional[bool] = None

    @classmethod
    def check_bubblewrap_working(cls) -> bool:
        """
        Check if bubblewrap actually works (not just installed).
        
        Returns:
            True if bubblewrap can create namespaces, False otherwise
        """
        if cls._bwrap_working is not None:
            return cls._bwrap_working
            
        if not cls.validate_bubblewrap_available():
            cls._bwrap_working = False
            return False
        
        # Test if bwrap can actually create namespaces
        try:
            result = subprocess.run(
                ["bwrap", "--ro-bind", "/", "/", "--", "echo", "test"],
                capture_output=True,
                timeout=2
            )
            cls._bwrap_working = (result.returncode == 0)
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
            cls._bwrap_working = False
            
        return cls._bwrap_working

    @staticmethod
    def create_resource_limiter(memory_mb: int, time_limit: float) -> Callable:
        """
        Create a function to set resource limits for subprocess.
        
        Args:
            memory_mb: Memory limit in megabytes
            time_limit: CPU time limit in seconds
            
        Returns:
            A callable to be used as preexec_fn in subprocess
        """
        def set_limits():
            try:
                # Set virtual memory limit
                mem_bytes = memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                
                # Set CPU time limit (soft and hard)
                cpu_hard_limit = int(time_limit) + 1
                resource.setrlimit(
                    resource.RLIMIT_CPU, 
                    (int(time_limit), cpu_hard_limit)
                )
                
                # Prevent fork bombs
                resource.setrlimit(resource.RLIMIT_NPROC, (16, 16))
                
            except (ValueError, OSError) as e:
                # If setting limits fails, the preexec_fn will cause subprocess to fail
                raise RuntimeError(f"Failed to set resource limits: {str(e)}")

        return set_limits

    @classmethod
    def build_bubblewrap_command(
        cls,
        workdir: str,
        runtime_cmd: List[str],
        internet_enabled: bool = False
    ) -> List[str]:
        """
        Build bubblewrap command for sandboxing.
        
        Args:
            workdir: Working directory containing user files
            runtime_cmd: Command to execute inside sandbox
            internet_enabled: Whether to allow internet access
            
        Returns:
            Complete command list for bubblewrap execution
        """
        cmd = [
            "bwrap",
            # Bind essential system directories (read-only)
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            # Bind runtime packages as read-only to the same path
            "--ro-bind", settings.packages_dir, settings.packages_dir,
            # Bind user code directory
            "--bind", workdir, "/app",
            # Set working directory
            "--chdir", "/app",
            # Minimal proc and dev
            "--proc", "/proc",
            "--dev", "/dev",
            # Add tmpfs for /tmp
            "--tmpfs", "/tmp",
            # Separate arguments from bind mounts
            "--"
        ]

        # Disable network if not allowed
        if not internet_enabled:
            # Insert before the "--" separator
            cmd.insert(-1, "--unshare-net")

        # Append the actual command to run (after the "--")
        cmd.extend(runtime_cmd)

        return cmd
    
    @staticmethod
    def build_direct_command(
        workdir: str,
        runtime_cmd: List[str]
    ) -> List[str]:
        """
        Build command without bubblewrap (fallback mode).
        Less secure but works in restricted environments.
        
        Args:
            workdir: Working directory containing user files
            runtime_cmd: Command to execute
            
        Returns:
            Command list for direct execution
        """
        # Just run the command directly in the workdir
        # The resource limits will still apply via preexec_fn
        return runtime_cmd

    @classmethod
    def validate_bubblewrap_available(cls) -> bool:
        """
        Check if bubblewrap is available on the system.
        
        Returns:
            True if bubblewrap is available, False otherwise
        """
        if cls._bwrap_available is not None:
            return cls._bwrap_available
            
        import shutil
        cls._bwrap_available = shutil.which("bwrap") is not None
        return cls._bwrap_available
