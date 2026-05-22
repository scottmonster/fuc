"""Helper utilities and test dataclasses for FUC tests."""

from dataclasses import dataclass
from pathlib import Path


# Test dataclasses for various scenarios

@dataclass
class DatabaseConfig:
    """Database configuration for testing nested configs."""
    host: str = "localhost"
    port: int = 5432
    username: str = "admin"
    password: str = "secret"
    database: str = "mydb"


@dataclass
class ServerConfig:
    """Server configuration for testing nested configs."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    timeout: float = 30.0


@dataclass
class LogConfig:
    """Logging configuration for testing nested configs."""
    level: str = "INFO"
    file: str = "/var/log/app.log"
    max_size: int = 10485760  # 10MB
    rotate: bool = True


@dataclass
class ComplexConfig:
    """Complex configuration with multiple nested levels."""
    app_name: str = "myapp"
    version: str = "1.0.0"
    debug: bool = False
    database: DatabaseConfig | None = None
    server: ServerConfig | None = None
    logging: LogConfig | None = None
    tags: list[str] | None = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.server is None:
            self.server = ServerConfig()
        if self.logging is None:
            self.logging = LogConfig()
        if self.tags is None:
            self.tags = []


@dataclass
class MinimalConfig:
    """Minimal configuration with single field."""
    value: str = "default"


@dataclass
class EmptyConfig:
    """Configuration with no default values."""
    required_field: str


# Utility functions

def create_fuc_content(*args: str) -> str:
    """Create .fuc file content from argument lines.
    
    Args:
        *args: Lines to include in the file
        
    Returns:
        Formatted .fuc file content
    """
    return "\n".join(args)


def create_cli_args(*args: str) -> list[str]:
    """Create CLI argument list.
    
    Args:
        *args: Arguments to include
        
    Returns:
        List of CLI arguments
    """
    return list(args)


def assert_dict_equal(actual: dict, expected: dict, path: str = ""):
    """Recursively assert dictionary equality with clear error messages.
    
    Args:
        actual: Actual dictionary
        expected: Expected dictionary
        path: Current path in nested dict (for error messages)
    """
    actual_keys = set(actual.keys())
    expected_keys = set(expected.keys())
    
    # Check for missing keys
    missing = expected_keys - actual_keys
    if missing:
        raise AssertionError(
            f"Missing keys at {path or 'root'}: {missing}"
        )
    
    # Check for extra keys
    extra = actual_keys - expected_keys
    if extra:
        raise AssertionError(
            f"Extra keys at {path or 'root'}: {extra}"
        )
    
    # Check values
    for key in expected_keys:
        current_path = f"{path}.{key}" if path else key
        actual_val = actual[key]
        expected_val = expected[key]
        
        if isinstance(expected_val, dict) and isinstance(actual_val, dict):
            assert_dict_equal(actual_val, expected_val, current_path)
        else:
            if actual_val != expected_val:
                raise AssertionError(
                    f"Value mismatch at {current_path}: "
                    f"expected {expected_val!r}, got {actual_val!r}"
                )


def write_config_file(path: Path, content: str):
    """Write content to a config file.
    
    Args:
        path: Path to write to
        content: Content to write
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
