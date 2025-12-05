"""
Code execution engine core.
"""
import os
import time
import uuid
import tempfile
import subprocess
import resource
from typing import Tuple
import logging

from app.models import ExecRequest, ExecResult, RunResult
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
        cpu_start = time.process_time()

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
                    language=request.language,
                    version=request.version,
                    run=RunResult(
                        stdout="",
                        stderr="",
                        output="",
                        code=127,
                        signal=None,
                        message=str(e),
                        status="error",
                        cpu_time=0,
                        wall_time=0,
                        memory=None
                    )
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
                    result_data = self._run_sandboxed_process(
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
                        language=request.language,
                        version=request.version,
                        run=RunResult(
                            stdout="",
                            stderr="",
                            output="",
                            code=1,
                            signal=None,
                            message=str(e),
                            status="error",
                            cpu_time=0,
                            wall_time=0,
                            memory=None
                        )
                    )
                except SandboxExecutionException as e:
                    logger.error(f"Sandbox error for job {job_id}: {str(e)}")
                    return ExecResult(
                        language=request.language,
                        version=request.version,
                        run=RunResult(
                            stdout="",
                            stderr=str(e),
                            output=str(e),
                            code=1,
                            signal=None,
                            message=str(e),
                            status="error",
                            cpu_time=0,
                            wall_time=0,
                            memory=None
                        )
                    )

            # Calculate execution time
            wall_time_ms = int((time.time() - start_time) * 1000)
            cpu_time_ms = int((time.process_time() - cpu_start) * 1000)
            
            # Truncate output if needed
            stdout = self.truncate_output(result_data['stdout'], settings.max_output_size, "stdout")
            stderr = self.truncate_output(result_data['stderr'], settings.max_stderr_size, "stderr")
            
            # Combine stdout and stderr for output field
            output = stdout if not stderr else (stdout + stderr if stdout else stderr)
            
            logger.info(f"Job {job_id} completed with exit code {result_data['exit_code']} in {wall_time_ms}ms")
            
            return ExecResult(
                language=request.language,
                version=request.version,
                run=RunResult(
                    stdout=stdout,
                    stderr=stderr,
                    output=output,
                    code=result_data['exit_code'],
                    signal=result_data.get('signal'),
                    message=None,
                    status=None,
                    cpu_time=cpu_time_ms,
                    wall_time=wall_time_ms,
                    memory=result_data.get('memory')
                )
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.exception(f"Unexpected error for job {job_id}")
            wall_time_ms = int((time.time() - start_time) * 1000)
            
            return ExecResult(
                language=request.language,
                version=request.version,
                run=RunResult(
                    stdout="",
                    stderr="",
                    output="",
                    code=1,
                    signal=None,
                    message=f"Internal error: {str(e)}",
                    status="error",
                    cpu_time=0,
                    wall_time=wall_time_ms,
                    memory=None
                )
            )

    def _run_sandboxed_process(
        self,
        command: list,
        workdir: str,
        stdin_data: str,
        memory_limit: int,
        time_limit: float,
        use_bwrap: bool = True
    ) -> dict:
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
            Dictionary with stdout, stderr, exit_code, signal, memory
            
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
            signal_name = None
            try:
                stdout, stderr = proc.communicate(
                    input=stdin_data,
                    timeout=time_limit + 0.5  # Add margin for cleanup
                )
                exit_code = proc.returncode
                
                # Check if process was terminated by signal
                if exit_code < 0:
                    signal_name = f"signal_{abs(exit_code)}"
                
            except subprocess.TimeoutExpired:
                # Kill process on timeout
                proc.kill()
                try:
                    stdout, stderr = proc.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    stdout, stderr = "", ""
                
                stderr = "TIMEOUT: Execution exceeded time limit\n" + stderr
                exit_code = 124  # Standard timeout exit code
                signal_name = "SIGKILL"
            
            # Try to get memory usage (rough estimate)
            try:
                rusage = resource.getrusage(resource.RUSAGE_CHILDREN)
                # maxrss is in KB on Linux, convert to bytes
                memory_bytes = rusage.ru_maxrss * 1024
            except:
                memory_bytes = None
                
        except OSError as e:
            raise SandboxExecutionException(
                f"Failed to execute sandboxed process: {str(e)}"
            )
        except Exception as e:
            raise SandboxExecutionException(
                f"Unexpected error during execution: {str(e)}"
            )

        return {
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': exit_code,
            'signal': signal_name,
            'memory': memory_bytes
        }
