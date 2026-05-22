"""Pytest fixtures for FUC tests."""

import os
import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Any


@pytest.fixture
def tmp_config_file(tmp_path):
    """Create a temporary .fuc config file with given content.
    
    Returns a function that takes content string and returns path.
    """
    def _create_file(content: str, filename: str = "test.fuc") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path
    return _create_file


@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for testing.
    
    Returns a function that takes key-value dict and sets env vars.
    """
    def _set_env(env_vars: dict[str, str]):
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
    return _set_env


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all FUC-related environment variables."""
    env_keys = [k for k in os.environ.keys() if k.startswith("FUC_")]
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def sample_schema():
    """Simple dataclass schema for testing."""
    @dataclass
    class SimpleConfig:
        name: str = "default"
        port: int = 8080
        debug: bool = False
    
    return SimpleConfig


@pytest.fixture
def nested_schema():
    """Nested dataclass schema for testing."""
    @dataclass
    class Database:
        host: str = "localhost"
        port: int = 5432
        name: str = "mydb"
    
    @dataclass
    class Server:
        host: str = "0.0.0.0"
        port: int = 8000
        workers: int = 4
    
    @dataclass
    class AppConfig:
        app_name: str = "myapp"
        debug: bool = False
        database: Database | None = None
        server: Server | None = None
        
        def __post_init__(self):
            if self.database is None:
                self.database = Database()
            if self.server is None:
                self.server = Server()
    
    return AppConfig


@pytest.fixture
def list_schema():
    """Schema with list fields for testing."""
    @dataclass
    class ListConfig:
        names: list[str] | None = None
        ports: list[int] | None = None
        ratios: list[float] | None = None
        
        def __post_init__(self):
            if self.names is None:
                self.names = []
            if self.ports is None:
                self.ports = [8080]
            if self.ratios is None:
                self.ratios = [0.5, 1.0]
    
    return ListConfig


@pytest.fixture
def all_types_schema():
    """Schema with all supported types for testing."""
    @dataclass
    class AllTypesConfig:
        str_val: str = "default"
        int_val: int = 42
        float_val: float = 3.14
        bool_val: bool = True
        list_str: list[str] | None = None
        list_int: list[int] | None = None
        list_float: list[float] | None = None
        
        def __post_init__(self):
            if self.list_str is None:
                self.list_str = ["a", "b"]
            if self.list_int is None:
                self.list_int = [1, 2, 3]
            if self.list_float is None:
                self.list_float = [1.1, 2.2]
    
    return AllTypesConfig


@pytest.fixture
def config_file_content():
    """Common config file content builder."""
    def _build(*lines: str) -> str:
        return "\n".join(lines)
    return _build
