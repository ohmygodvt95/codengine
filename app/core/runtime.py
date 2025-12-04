"""
Runtime management for different programming languages.
"""
import os
from typing import List
from app.exceptions import RuntimeNotFoundException, UnsupportedLanguageException
from app.config import settings

class RuntimeManager:
    """Manages runtime environments for different languages."""
    
    SUPPORTED_LANGUAGES = {
        'python': {
            'base_dir': settings.packages_dir + '/python',
            'binary_names': ['python3', 'python'],
            'bin_subdir': 'bin'
        },
        'node': {
            'base_dir': settings.packages_dir + '/node',
            'binary_names': ['node'],
            'bin_subdir': 'bin'
        }
    }

    @staticmethod
    def find_version_dir(base_dir: str, requested_version: str) -> str:
        """
        Find the runtime version directory.
        
        Args:
            base_dir: Base directory for the language runtimes
            requested_version: Requested version (e.g., "3.11" or "3.11.9")
            
        Returns:
            Full path to the version directory
            
        Raises:
            RuntimeNotFoundException: If the version is not found
        """
        # Check if exact version exists
        exact_path = os.path.join(base_dir, requested_version)
        if os.path.isdir(exact_path):
            return exact_path

        # Fallback: find directory with matching prefix
        if os.path.isdir(base_dir):
            candidates = sorted(
                d for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d)) 
                and d.startswith(requested_version)
            )
            if candidates:
                # Return the latest version (last in sorted list)
                return os.path.join(base_dir, candidates[-1])

        raise RuntimeNotFoundException(
            f"Runtime version '{requested_version}' not found in {base_dir}"
        )

    @staticmethod
    def get_runtime_command(language: str, version: str) -> List[str]:
        """
        Get the command to execute code for a specific language and version.
        
        Args:
            language: Programming language (e.g., 'python', 'node')
            version: Version string (e.g., '3.11.9', '18.0.0')
            
        Returns:
            List containing the full path to the runtime binary
            
        Raises:
            UnsupportedLanguageException: If the language is not supported
            RuntimeNotFoundException: If the runtime binary is not found
        """
        language = language.lower()
        
        if language not in RuntimeManager.SUPPORTED_LANGUAGES:
            raise UnsupportedLanguageException(
                f"Language '{language}' is not supported. "
                f"Supported languages: {', '.join(RuntimeManager.SUPPORTED_LANGUAGES.keys())}"
            )

        lang_config = RuntimeManager.SUPPORTED_LANGUAGES[language]
        base_dir = lang_config['base_dir']
        
        try:
            version_dir = RuntimeManager.find_version_dir(base_dir, version)
        except RuntimeNotFoundException as e:
            raise RuntimeNotFoundException(
                f"Runtime for {language} version {version} not found: {str(e)}"
            )

        # Try to find the binary
        bin_dir = os.path.join(version_dir, lang_config['bin_subdir'])
        
        for binary_name in lang_config['binary_names']:
            binary_path = os.path.join(bin_dir, binary_name)
            if os.path.exists(binary_path) and os.access(binary_path, os.X_OK):
                return [binary_path]

        raise RuntimeNotFoundException(
            f"No executable binary found in {bin_dir}. "
            f"Tried: {', '.join(lang_config['binary_names'])}"
        )
