"""Tests for error handling and error classes."""

import pytest
from dataclasses import dataclass
from fuc import Fuc
from fuc.errors import (
    FucError,
    ParseError,
    TypeCastError,
    DuplicateKeyError,
    UnknownKeyError
)


@dataclass
class SimpleConfig:
    """Simple config for error testing."""
    name: str = "default"
    port: int = 8080
    enabled: bool = True


class TestFucError:
    """Test base FucError class."""
    
    def test_fuc_error_is_exception(self):
        """Test FucError is an Exception."""
        error = FucError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"
    
    def test_all_errors_inherit_fuc_error(self):
        """Test all error classes inherit from FucError."""
        assert issubclass(ParseError, FucError)
        assert issubclass(TypeCastError, FucError)
        assert issubclass(DuplicateKeyError, FucError)
        assert issubclass(UnknownKeyError, FucError)


class TestParseError:
    """Test ParseError class."""
    
    def test_parse_error_invalid_format(self, tmp_path, clean_env):
        """Test ParseError raised for invalid format."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("invalid format without dashes\n")
        
        with pytest.raises(ParseError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_parse_error_malformed_line(self, tmp_path, clean_env):
        """Test ParseError for malformed lines."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--name\n")  # Missing value
        
        with pytest.raises(ParseError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_parse_error_message_context(self, tmp_path, clean_env):
        """Test ParseError includes contextual information."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--name\n")
        
        with pytest.raises(ParseError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        
        # Error should mention the key
        error_msg = str(exc_info.value)
        assert "name" in error_msg.lower() or "missing" in error_msg.lower()


class TestTypeCastError:
    """Test TypeCastError class."""
    
    def test_type_cast_error_int(self, tmp_path, clean_env):
        """Test TypeCastError for invalid integer."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--port not_an_int\n")
        
        with pytest.raises(TypeCastError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_type_cast_error_bool(self, tmp_path, clean_env):
        """Test TypeCastError for invalid boolean."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--enabled maybe\n")
        
        with pytest.raises(TypeCastError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_type_cast_error_float(self, clean_env):
        """Test TypeCastError for invalid float."""
        @dataclass
        class FloatConfig:
            value: float = 1.0
        
        with pytest.raises(TypeCastError):
            Fuc(FloatConfig, "testapp", cli_args=["--value", "not_a_float"])
    
    def test_type_cast_error_message_includes_expected_type(self, tmp_path, clean_env):
        """Test TypeCastError message includes expected type."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--port abc\n")
        
        with pytest.raises(TypeCastError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        
        error_msg = str(exc_info.value)
        # Should mention int type or conversion
        assert "int" in error_msg.lower() or "integer" in error_msg.lower() or "convert" in error_msg.lower()


class TestDuplicateKeyError:
    """Test DuplicateKeyError class."""
    
    def test_duplicate_key_in_file(self, tmp_path, clean_env):
        """Test DuplicateKeyError for duplicate keys in file."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--name first\n--name second\n")
        
        with pytest.raises(DuplicateKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_duplicate_key_message_includes_key(self, tmp_path, clean_env):
        """Test DuplicateKeyError message includes the key name."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--port 8080\n--port 9090\n")
        
        with pytest.raises(DuplicateKeyError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        
        error_msg = str(exc_info.value)
        assert "port" in error_msg.lower() or "duplicate" in error_msg.lower()
    
    def test_duplicate_key_includes_source(self, tmp_path, clean_env):
        """Test DuplicateKeyError mentions source file."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--name first\n--name second\n")
        
        with pytest.raises(DuplicateKeyError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        
        error_msg = str(exc_info.value)
        # Should mention file or source
        assert "config.fuc" in error_msg or "file" in error_msg.lower()


class TestUnknownKeyError:
    """Test UnknownKeyError class."""
    
    def test_unknown_key_in_file(self, tmp_path, clean_env):
        """Test UnknownKeyError for keys not in schema."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--nonexistent value\n")
        
        with pytest.raises(UnknownKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_unknown_key_in_cli(self, clean_env):
        """Test UnknownKeyError for CLI args not in schema."""
        with pytest.raises(UnknownKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--invalid_option", "value"])
    
    def test_unknown_key_message_includes_key(self, clean_env):
        """Test UnknownKeyError message includes the unknown key."""
        with pytest.raises(UnknownKeyError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--bad_key", "value"])
        
        error_msg = str(exc_info.value)
        assert "bad_key" in error_msg.lower() or "unknown" in error_msg.lower()
    
    def test_unknown_key_suggests_similar(self, clean_env):
        """Test UnknownKeyError suggests similar valid keys."""
        with pytest.raises(UnknownKeyError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--nam", "value"])  # Similar to 'name'
        
        error_msg = str(exc_info.value)
        # Should suggest 'name'
        assert "name" in error_msg.lower() or "suggestion" in error_msg.lower() or "did you mean" in error_msg.lower()


class TestErrorContext:
    """Test error context and debugging information."""
    
    def test_error_includes_line_number(self, tmp_path, clean_env):
        """Test errors include line numbers when possible."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("# Comment\n--name valid\n--port invalid\n")
        
        with pytest.raises(TypeCastError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        
        error_msg = str(exc_info.value)
        # Should mention line 3 or similar context
        assert "3" in error_msg or "line" in error_msg.lower()
    
    def test_error_includes_source_name(self, tmp_path, clean_env):
        """Test errors include source file name."""
        config_file = tmp_path / "myconfig.fuc"
        config_file.write_text("--unknown key\n")
        
        with pytest.raises(UnknownKeyError) as exc_info:
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        
        error_msg = str(exc_info.value)
        assert "myconfig.fuc" in error_msg or "file" in error_msg.lower()


class TestNestedKeyErrors:
    """Test errors for nested key access."""
    
    def test_invalid_nested_key(self, clean_env):
        """Test error for invalid nested key syntax."""
        @dataclass
        class NestedConfig:
            @dataclass
            class Database:
                host: str = "localhost"
            
            database: Database | None = None
            
            def __post_init__(self):
                if self.database is None:
                    self.database = self.Database()
        
        with pytest.raises(UnknownKeyError):
            Fuc(NestedConfig, "testapp", cli_args=["--database.invalid", "value"])
    
    def test_nested_unknown_key_message(self, clean_env):
        """Test UnknownKeyError message for nested keys."""
        @dataclass
        class NestedConfig:
            @dataclass
            class Database:
                host: str = "localhost"
            
            database: Database | None = None
            
            def __post_init__(self):
                if self.database is None:
                    self.database = self.Database()
        
        with pytest.raises(UnknownKeyError) as exc_info:
            Fuc(NestedConfig, "testapp", cli_args=["--database.bad", "value"])
        
        error_msg = str(exc_info.value)
        assert "database.bad" in error_msg.lower() or "bad" in error_msg.lower()
