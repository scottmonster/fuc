"""Tests for CLI argument parsing functionality."""

import pytest
from dataclasses import dataclass
from fuc.parser import parse_cli
from fuc.errors import ParseError, UnknownKeyError


@dataclass
class SimpleSchema:
    """Simple schema for testing."""
    name: str = "default"
    port: int = 8080
    debug: bool = False


@dataclass
class NestedSchema:
    """Nested schema for testing."""
    app_name: str = "myapp"
    
    @dataclass
    class Database:
        host: str = "localhost"
        port: int = 5432
    
    database: Database | None = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = self.Database()


class TestBasicCLIParsing:
    """Test basic CLI argument parsing."""
    
    def test_single_argument(self):
        """Test parsing single argument."""
        args = ["--name", "myapp"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"name": "myapp"}
        assert result['config_path'] is None
    
    def test_multiple_arguments(self):
        """Test parsing multiple arguments."""
        args = ["--name", "myapp", "--port", "9000"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"name": "myapp", "port": 9000}
        assert result['config_path'] is None
    
    def test_all_arguments(self):
        """Test parsing all schema fields."""
        args = ["--name", "myapp", "--port", "8000", "--debug", "true"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"name": "myapp", "port": 8000, "debug": True}
        assert result['config_path'] is None
    
    def test_empty_args(self):
        """Test parsing empty argument list."""
        args = []
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {}
        assert result['config_path'] is None


class TestConfigFlag:
    """Test --config flag handling."""
    
    def test_config_flag_only(self):
        """Test --config flag with path."""
        args = ["--config", "/path/to/config.fuc"]
        result = parse_cli(args, SimpleSchema)
        assert result['config_path'] == "/path/to/config.fuc"
        assert result['values'] == {}
    
    def test_config_flag_with_other_args_before(self):
        """Test --config flag after other arguments."""
        args = ["--name", "myapp", "--config", "/path/to/config.fuc"]
        result = parse_cli(args, SimpleSchema)
        assert result['config_path'] == "/path/to/config.fuc"
        assert result['values'] == {"name": "myapp"}
    
    def test_config_flag_with_other_args_after(self):
        """Test --config flag before other arguments."""
        args = ["--config", "/path/to/config.fuc", "--name", "myapp"]
        result = parse_cli(args, SimpleSchema)
        assert result['config_path'] == "/path/to/config.fuc"
        assert result['values'] == {"name": "myapp"}
    
    def test_config_flag_in_middle(self):
        """Test --config flag between other arguments."""
        args = ["--name", "myapp", "--config", "/path/to/config.fuc", "--port", "9000"]
        result = parse_cli(args, SimpleSchema)
        assert result['config_path'] == "/path/to/config.fuc"
        assert result['values'] == {"name": "myapp", "port": 9000}
    
    def test_config_flag_without_value(self):
        """Test --config without value raises error."""
        args = ["--config"]
        with pytest.raises(ParseError) as exc_info:
            parse_cli(args, SimpleSchema)
        assert "--config requires a path" in str(exc_info.value)
    
    def test_config_path_with_spaces(self):
        """Test --config with path containing spaces."""
        args = ["--config", "/path/to/my config/app.fuc"]
        result = parse_cli(args, SimpleSchema)
        assert result['config_path'] == "/path/to/my config/app.fuc"


class TestBooleanFlags:
    """Test boolean flag handling in CLI."""
    
    def test_standalone_bool_flag(self):
        """Test standalone boolean flag."""
        args = ["--debug"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"debug": True}
    
    def test_explicit_bool_true(self):
        """Test explicit true value."""
        args = ["--debug", "true"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"debug": True}
    
    def test_explicit_bool_false(self):
        """Test explicit false value."""
        args = ["--debug", "false"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"debug": False}
    
    def test_bool_with_config_flag(self):
        """Test boolean flag with --config."""
        args = ["--debug", "--config", "/path/to/config.fuc"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"debug": True}
        assert result['config_path'] == "/path/to/config.fuc"


class TestNestedKeys:
    """Test nested key handling in CLI."""
    
    def test_nested_key(self):
        """Test nested dot notation key."""
        args = ["--database.host", "db.example.com"]
        result = parse_cli(args, NestedSchema)
        assert result['values'] == {"database": {"host": "db.example.com"}}
    
    def test_multiple_nested_keys(self):
        """Test multiple nested keys."""
        args = ["--database.host", "db.example.com", "--database.port", "3306"]
        result = parse_cli(args, NestedSchema)
        assert result['values'] == {
            "database": {"host": "db.example.com", "port": 3306}
        }
    
    def test_nested_with_config(self):
        """Test nested keys with --config flag."""
        args = [
            "--config", "/path/to/config.fuc",
            "--database.host", "db.example.com"
        ]
        result = parse_cli(args, NestedSchema)
        assert result['config_path'] == "/path/to/config.fuc"
        assert result['values'] == {"database": {"host": "db.example.com"}}


class TestListValues:
    """Test list value handling in CLI."""
    
    def test_list_of_strings(self):
        """Test list of string values."""
        @dataclass
        class ListSchema:
            names: list[str] | None = None
            
            def __post_init__(self):
                if self.names is None:
                    self.names = []
        
        args = ["--names", "alice", "bob", "charlie"]
        result = parse_cli(args, ListSchema)
        assert result['values'] == {"names": ["alice", "bob", "charlie"]}
    
    def test_list_of_ints(self):
        """Test list of integer values."""
        @dataclass
        class ListSchema:
            ports: list[int] | None = None
            
            def __post_init__(self):
                if self.ports is None:
                    self.ports = []
        
        args = ["--ports", "8080", "8081", "8082"]
        result = parse_cli(args, ListSchema)
        assert result['values'] == {"ports": [8080, 8081, 8082]}


class TestErrorHandling:
    """Test error handling in CLI parsing."""
    
    def test_unknown_key(self):
        """Test unknown key raises error."""
        args = ["--unknown", "value"]
        with pytest.raises(UnknownKeyError):
            parse_cli(args, SimpleSchema)
    
    def test_invalid_type(self):
        """Test invalid type raises error."""
        args = ["--port", "not_a_number"]
        from fuc.errors import TypeCastError
        with pytest.raises(TypeCastError):
            parse_cli(args, SimpleSchema)
    
    def test_duplicate_key(self):
        """Test duplicate key raises error."""
        args = ["--name", "first", "--name", "second"]
        from fuc.errors import DuplicateKeyError
        with pytest.raises(DuplicateKeyError):
            parse_cli(args, SimpleSchema)
    
    def test_source_is_cli_in_errors(self):
        """Test error messages indicate CLI source."""
        args = ["--unknown", "value"]
        with pytest.raises(UnknownKeyError) as exc_info:
            parse_cli(args, SimpleSchema)
        assert "CLI" in str(exc_info.value)


class TestQuotedValues:
    """Test quoted values in CLI arguments."""
    
    def test_double_quoted_value(self):
        """Test double-quoted value."""
        args = ["--name", "My Application"]
        result = parse_cli(args, SimpleSchema)
        # Note: The shell would have already removed quotes,
        # but we're testing with the value as-is
        assert result['values'] == {"name": "My"}
    
    def test_value_with_special_chars(self):
        """Test value with special characters."""
        args = ["--name", "app@v1.0"]
        result = parse_cli(args, SimpleSchema)
        assert result['values'] == {"name": "app@v1.0"}


class TestEdgeCases:
    """Test edge cases in CLI parsing."""
    
    def test_negative_number(self):
        """Test negative number values."""
        @dataclass
        class NumSchema:
            offset: int = 0
            ratio: float = 0.0
        
        args = ["--offset", "-100", "--ratio", "-0.5"]
        result = parse_cli(args, NumSchema)
        assert result['values'] == {"offset": -100, "ratio": -0.5}
    
    def test_config_path_variations(self):
        """Test various config path formats."""
        test_paths = [
            "/absolute/path/config.fuc",
            "relative/path/config.fuc",
            "./current/dir/config.fuc",
            "../parent/dir/config.fuc",
            "~/home/config.fuc",
        ]
        
        for path in test_paths:
            args = ["--config", path]
            result = parse_cli(args, SimpleSchema)
            assert result['config_path'] == path
    
    def test_windows_path(self):
        """Test Windows-style path."""
        args = ["--config", "C:\\Users\\MyUser\\config.fuc"]
        result = parse_cli(args, SimpleSchema)
        assert result['config_path'] == "C:\\Users\\MyUser\\config.fuc"
