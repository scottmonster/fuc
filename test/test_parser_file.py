"""Tests for file parsing functionality."""

import pytest
from pathlib import Path
from dataclasses import dataclass
from fuc.parser import parse_file
from fuc.errors import ParseError, UnknownKeyError, TypeCastError


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
    class Server:
        host: str = "localhost"
        port: int = 8000
    
    server: Server | None = None
    
    def __post_init__(self):
        if self.server is None:
            self.server = self.Server()


class TestBasicFileParsing:
    """Test basic file parsing."""
    
    def test_single_line_config(self, tmp_config_file):
        """Test parsing single line config file."""
        config = tmp_config_file("--name myapp")
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp"}
    
    def test_multiple_lines(self, tmp_config_file):
        """Test parsing multiple lines."""
        config = tmp_config_file(
            "--name myapp\n"
            "--port 9000\n"
            "--debug true"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000, "debug": True}
    
    def test_multiple_values_on_same_line(self, tmp_config_file):
        """Test multiple key-value pairs on same line."""
        config = tmp_config_file("--name myapp --port 9000")
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000}


class TestComments:
    """Test comment handling."""
    
    def test_comment_only_line(self, tmp_config_file):
        """Test lines with only comments are ignored."""
        config = tmp_config_file(
            "# This is a comment\n"
            "--name myapp"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp"}
    
    def test_multiple_comment_lines(self, tmp_config_file):
        """Test multiple comment lines."""
        config = tmp_config_file(
            "# Comment 1\n"
            "# Comment 2\n"
            "--name myapp\n"
            "# Comment 3\n"
            "--port 9000"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000}
    
    def test_comment_with_hash_symbols(self, tmp_config_file):
        """Test comments with multiple hash symbols."""
        config = tmp_config_file(
            "### Header Comment ###\n"
            "--name myapp"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp"}


class TestBlankLines:
    """Test blank line handling."""
    
    def test_blank_lines_ignored(self, tmp_config_file):
        """Test blank lines are ignored."""
        config = tmp_config_file(
            "--name myapp\n"
            "\n"
            "--port 9000"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000}
    
    def test_multiple_blank_lines(self, tmp_config_file):
        """Test multiple consecutive blank lines."""
        config = tmp_config_file(
            "--name myapp\n"
            "\n"
            "\n"
            "\n"
            "--port 9000"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000}
    
    def test_whitespace_only_lines(self, tmp_config_file):
        """Test lines with only whitespace are treated as blank."""
        config = tmp_config_file(
            "--name myapp\n"
            "   \n"
            "\t\n"
            "  \t  \n"
            "--port 9000"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000}


class TestMixedContent:
    """Test files with mixed comments, blank lines, and config."""
    
    def test_typical_config_file(self, tmp_config_file):
        """Test a typical config file with comments and sections."""
        config = tmp_config_file(
            "# Application Configuration\n"
            "\n"
            "# Basic settings\n"
            "--name myapp\n"
            "--debug true\n"
            "\n"
            "# Server settings\n"
            "--port 9000\n"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "debug": True, "port": 9000}
    
    def test_comments_between_values(self, tmp_config_file):
        """Test comments between configuration values."""
        config = tmp_config_file(
            "--name myapp\n"
            "# Change port\n"
            "--port 9000\n"
            "# Enable debug\n"
            "--debug true"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp", "port": 9000, "debug": True}


class TestNestedConfig:
    """Test parsing nested configuration."""
    
    def test_nested_keys(self, tmp_config_file):
        """Test nested dot notation keys."""
        config = tmp_config_file(
            "--app_name myapp\n"
            "--server.host 0.0.0.0\n"
            "--server.port 8080"
        )
        result = parse_file(str(config), NestedSchema)
        assert result == {
            "app_name": "myapp",
            "server": {"host": "0.0.0.0", "port": 8080}
        }


class TestQuotedValues:
    """Test quoted values in config files."""
    
    def test_double_quoted_value(self, tmp_config_file):
        """Test double-quoted values."""
        config = tmp_config_file('--name "My Application"')
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "My Application"}
    
    def test_single_quoted_value(self, tmp_config_file):
        """Test single-quoted values."""
        config = tmp_config_file("--name 'My Application'")
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "My Application"}
    
    def test_path_with_spaces(self, tmp_config_file):
        """Test file paths with spaces."""
        @dataclass
        class PathSchema:
            config_path: str = "/default/path"
        
        config = tmp_config_file('--config_path "/home/user/my configs/app.fuc"')
        result = parse_file(str(config), PathSchema)
        assert result == {"config_path": "/home/user/my configs/app.fuc"}


class TestErrorHandling:
    """Test error handling in file parsing."""
    
    def test_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            parse_file("/nonexistent/file.fuc", SimpleSchema)
        assert "not found" in str(exc_info.value)
    
    def test_unknown_key_in_file(self, tmp_config_file):
        """Test unknown key raises UnknownKeyError."""
        config = tmp_config_file("--unknown_key value")
        with pytest.raises(UnknownKeyError) as exc_info:
            parse_file(str(config), SimpleSchema)
        assert "unknown_key" in str(exc_info.value)
        # Source should be the file path
        assert str(config) in str(exc_info.value)
    
    def test_invalid_type_in_file(self, tmp_config_file):
        """Test invalid type raises TypeCastError."""
        config = tmp_config_file("--port not_a_number")
        with pytest.raises(TypeCastError) as exc_info:
            parse_file(str(config), SimpleSchema)
        assert "port" in str(exc_info.value)
    
    def test_duplicate_key_in_file(self, tmp_config_file):
        """Test duplicate keys in file."""
        config = tmp_config_file(
            "--name first\n"
            "--name second"
        )
        from fuc.errors import DuplicateKeyError
        with pytest.raises(DuplicateKeyError) as exc_info:
            parse_file(str(config), SimpleSchema)
        assert "name" in str(exc_info.value)


class TestEmptyFiles:
    """Test handling of empty or comment-only files."""
    
    def test_empty_file(self, tmp_config_file):
        """Test empty file returns empty dict."""
        config = tmp_config_file("")
        result = parse_file(str(config), SimpleSchema)
        assert result == {}
    
    def test_comment_only_file(self, tmp_config_file):
        """Test file with only comments returns empty dict."""
        config = tmp_config_file(
            "# Comment 1\n"
            "# Comment 2\n"
            "# Comment 3"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {}
    
    def test_blank_lines_only(self, tmp_config_file):
        """Test file with only blank lines returns empty dict."""
        config = tmp_config_file("\n\n\n")
        result = parse_file(str(config), SimpleSchema)
        assert result == {}


class TestMultilineValues:
    """Test values that span multiple lines (via separate keys)."""
    
    def test_list_across_lines(self, tmp_config_file):
        """Test that list values on one line work."""
        @dataclass
        class ListSchema:
            names: list[str] | None = None
            
            def __post_init__(self):
                if self.names is None:
                    self.names = []
        
        config = tmp_config_file('--names alice bob charlie')
        result = parse_file(str(config), ListSchema)
        assert result == {"names": ["alice", "bob", "charlie"]}


class TestUnicode:
    """Test unicode character handling."""
    
    def test_unicode_in_values(self, tmp_config_file):
        """Test unicode characters in config values."""
        config = tmp_config_file('--name "Café ☕"')
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "Café ☕"}
    
    def test_unicode_in_comments(self, tmp_config_file):
        """Test unicode in comments doesn't cause issues."""
        config = tmp_config_file(
            "# Configuration pour café ☕\n"
            "--name myapp"
        )
        result = parse_file(str(config), SimpleSchema)
        assert result == {"name": "myapp"}
