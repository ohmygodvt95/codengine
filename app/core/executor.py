"""
Code execution engine core.
"""
import os
import time
import uuid
import tempfile
import subprocess
from typing import Tuple
import logging

from app.models import ExecRequest, ExecResult
from app.core.runtime import RuntimeManager
from app.core.sandbox import SandboxManager
from app.config import settings
from app.exceptions import (
    CodeEngineException,
    RuntimeNotFoundException,
    UnsupportedLanguageException,
    SandboxExecutionException,
    FileSystemException
)

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Handles code execution in a sandboxed environment."""

    def __init__(self):
        self.runtime_manager = RuntimeManager()
        self.sandbox_manager = SandboxManager()

    @staticmethod
    def truncate_output(output: str, max_size: int, label: str = "output") -> str:
        """
        Truncate output if it exceeds the maximum size.
        
        Args:
            output: Output string to truncate
            max_size: Maximum size in bytes
            label: Label for the truncation message (stdout/stderr)
            
        Returns:
            Truncated output with warning message if needed
        """
        output_bytes = output.encode('utf-8')
        if len(output_bytes) <= max_size:
            return output
        
        # Truncate and add warning
        truncated = output_bytes[:max_size].decode('utf-8', errors='ignore')
        warning = f"\n\n[TRUNCATED: {label} exceeded {max_size} bytes ({max_size // 1024} KB)]\n"
        
        # Make room for the warning message
        warning_size = len(warning.encode('utf-8'))
        if len(output_bytes) > max_size - warning_size:
            truncated = output_bytes[:max_size - warning_size].decode('utf-8', errors='ignore')
        
        return truncated + warning

    def prepare_workspace(self, files: list, workdir: str) -> None:
        """
        Prepare workspace by writing all files to the temporary directory.
        
        Args:
            files: List of File objects containing name and content
            workdir: Temporary directory path
            
        Raises:
            FileSystemException: If file writing fails
        """
        try:
            for file in files:
                file_path = os.path.join(workdir, file.name)
                
                # Create parent directories if needed
                parent_dir = os.path.dirname(file_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                
                # Write file content
                with open(file_path, 'w', encoding='utf-8') as fp:
                    fp.write(file.content)
                    
                logger.debug(f"Created file: {file_path}")
                
        except (OSError, IOError) as e:
            raise FileSystemException(f"Failed to prepare workspace: {str(e)}")

    def execute_code(self, request: ExecRequest) -> ExecResult:
        """
        Execute code in a sandboxed environment.
        
        Args:
            request: ExecRequest containing all execution parameters
            
        Returns:
            ExecResult with execution output and metadata
        """
        job_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Get runtime command
            try:
                runtime_cmd = self.runtime_manager.get_runtime_command(
                    request.language, 
                    request.version
                )
            except (RuntimeNotFoundException, UnsupportedLanguageException) as e:
                logger.error(f"Runtime error for job {job_id}: {str(e)}")
                return ExecResult(
                    stdout="",
                    stderr="",
                    exit_code=127,
                    time=0.0,
                    job_id=job_id,
                    error=str(e)
                )

            # Create temporary workspace
            with tempfile.TemporaryDirectory() as workdir:
                try:
                    # Prepare files in workspace
                    self.prepare_workspace(request.files, workdir)
                    
                    # Build command to execute
                    # First file is the main file to execute
                    main_file = request.files[0].name
                    cmd_inside = runtime_cmd + [main_file] + (request.args or [])
                    
                    # Check if bubblewrap is working
                    use_bwrap = self.sandbox_manager.check_bubblewrap_working()
                    
                    if use_bwrap:
                        # Build sandboxed command with bubblewrap
                        full_cmd = self.sandbox_manager.build_bubblewrap_command(
                            workdir=workdir,
                            runtime_cmd=cmd_inside,
                            internet_enabled=request.internet
                        )
                        logger.info(f"Executing job {job_id}: {request.language} {request.version} (sandboxed)")
                    else:
                        # Fallback: direct execution without bubblewrap
                        full_cmd = self.sandbox_manager.build_direct_command(
                            workdir=workdir,
                            runtime_cmd=cmd_inside
                        )
                        logger.warning(f"Executing job {job_id}: {request.language} {request.version} (direct mode - bubblewrap unavailable)")
                    
                    # Execute with resource limits
                    stdout, stderr, exit_code = self._run_sandboxed_process(
                        full_cmd,
                        workdir=workdir,
                        stdin_data=request.stdin,
                        memory_limit=request.memory_limit,
                        time_limit=request.time_limit,
                        use_bwrap=use_bwrap
                    )
                    
                except FileSystemException as e:
                    logger.error(f"Filesystem error for job {job_id}: {str(e)}")
                    return ExecResult(
                        stdout="",
                        stderr="",
                        exit_code=1,
                        time=0.0,
                        job_id=job_id,
                        error=str(e)
                    )
                except SandboxExecutionException as e:
                    logger.error(f"Sandbox error for job {job_id}: {str(e)}")
                    return ExecResult(
                        stdout="",
                        stderr=str(e),
                        exit_code=1,
                        time=0.0,
                        job_id=job_id,
                        error=str(e)
                    )

            # Calculate execution time
            elapsed = round(time.time() - start_time, 4)
            
            # Truncate output if needed
            stdout = self.truncate_output(stdout, settings.max_output_size, "stdout")
            stderr = self.truncate_output(stderr, settings.max_stderr_size, "stderr")
            
            logger.info(f"Job {job_id} completed with exit code {exit_code} in {elapsed}s")
            
            return ExecResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                time=elapsed,
                job_id=job_id,
                error=None
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.exception(f"Unexpected error for job {job_id}")
            elapsed = round(time.time() - start_time, 4)
            
            return ExecResult(
                stdout="",
                stderr="",
                exit_code=1,
                time=elapsed,
                job_id=job_id,
                error=f"Internal error: {str(e)}"
            )

    def _run_sandboxed_process(
        self,
        command: list,
        workdir: str,
        stdin_data: str,
        memory_limit: int,
        time_limit: float,
        use_bwrap: bool = True
    ) -> Tuple[str, str, int]:
        """
        Run a command in a sandboxed process with resource limits.
        
        Args:
            command: Command list to execute
            workdir: Working directory for the process
            stdin_data: Input data for stdin
            memory_limit: Memory limit in MB
            time_limit: Time limit in seconds
            use_bwrap: Whether bubblewrap is being used
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
            
        Raises:
            SandboxExecutionException: If execution fails
        """
        try:
            # Create resource limiter
            limiter = self.sandbox_manager.create_resource_limiter(
                memory_limit, 
                time_limit
            )
            
            # Prepare process arguments
            process_args = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "preexec_fn": limiter
            }
            
            # If not using bubblewrap, set cwd to workdir
            if not use_bwrap:
                process_args["cwd"] = workdir
            
            # Start process
            proc = subprocess.Popen(command, **process_args)
            
            # Communicate with timeout
            try:
                stdout, stderr = proc.communicate(
                    input=stdin_data,
                    timeout=time_limit + 0.5  # Add margin for cleanup
                )
                exit_code = proc.returncode
                
            except subprocess.TimeoutExpired:
                # Kill process on timeout
                proc.kill()
                try:
                    stdout, stderr = proc.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    stdout, stderr = "", ""
                
                stderr = "TIMEOUT: Execution exceeded time limit\n" + stderr
                exit_code = 124  # Standard timeout exit code
                
        except OSError as e:
            raise SandboxExecutionException(
                f"Failed to execute sandboxed process: {str(e)}"
            )
        except Exception as e:
            raise SandboxExecutionException(
                f"Unexpected error during execution: {str(e)}"
            )

        return stdout, stderr, exit_code
