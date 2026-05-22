"""Tests for Fuc config write functionality."""

import pytest
from pathlib import Path
from dataclasses import dataclass
from fuc import Fuc


@dataclass
class SimpleConfig:
    """Simple test config."""
    name: str = "default"
    port: int = 8080
    debug: bool = False


@dataclass
class NestedConfig:
    """Config with nesting."""
    app_name: str = "myapp"
    
    @dataclass
    class Server:
        """Server settings."""
        host: str = "localhost"
        port: int = 8000
    
    server: Server | None = None
    
    def __post_init__(self):
        if self.server is None:
            self.server = self.Server()


@dataclass
class ListConfig:
    """Config with list fields."""
    names: list[str] | None = None
    ports: list[int] | None = None
    ratios: list[float] | None = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = ["alice", "bob"]
        if self.ports is None:
            self.ports = [8080, 8081]
        if self.ratios is None:
            self.ratios = [0.5, 1.0]


class TestBasicWrite:
    """Test basic write functionality."""
    
    def test_write_to_file(self, clean_env, tmp_path):
        """Test writing config to file."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "myapp", "--port", "9000"])
        
        output_file = tmp_path / "output.fuc"
        config.write(str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "--name myapp" in content
        assert "--port 9000" in content
    
    def test_write_creates_parent_dirs(self, clean_env, tmp_path):
        """Test write creates parent directories if needed."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "subdir" / "nested" / "config.fuc"
        config.write(str(output_file))
        
        assert output_file.exists()
    
    def test_write_overwrites_existing(self, clean_env, tmp_path):
        """Test write overwrites existing file."""
        output_file = tmp_path / "config.fuc"
        output_file.write_text("old content")
        
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "newapp"])
        config.write(str(output_file))
        
        content = output_file.read_text()
        assert "old content" not in content
        assert "--name newapp" in content


class TestWriteWithNested:
    """Test writing nested configuration."""
    
    def test_write_nested_config(self, clean_env, tmp_path):
        """Test writing nested configuration."""
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--server.host", "0.0.0.0", "--server.port", "3000"]
        )
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        assert "--server.host 0.0.0.0" in content
        assert "--server.port 3000" in content


class TestWriteWithLists:
    """Test writing list values."""
    
    def test_write_list_str(self, clean_env, tmp_path):
        """Test writing list[str] values."""
        config = Fuc(ListConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        # list[str] should be quoted and space-separated
        assert '--names "alice" "bob"' in content
    
    def test_write_list_int(self, clean_env, tmp_path):
        """Test writing list[int] values."""
        config = Fuc(ListConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        # list[int] should be space-separated numbers
        assert "--ports 8080 8081" in content
    
    def test_write_list_float(self, clean_env, tmp_path):
        """Test writing list[float] values."""
        config = Fuc(ListConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        # list[float] should be space-separated floats
        assert "--ratios 0.5 1.0" in content


class TestWriteWithComments:
    """Test writing with docstring comments."""
    
    def test_docstrings_as_comments(self, clean_env, tmp_path):
        """Test dataclass docstrings appear as comments."""
        config = Fuc(NestedConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        # Docstrings should appear as comments
        assert "# Config with nesting" in content or "# Server settings" in content
    
    def test_comment_grouping(self, clean_env, tmp_path):
        """Test that related fields are grouped under same comment."""
        @dataclass
        class GroupedConfig:
            """Main config."""
            name: str = "app"
            
            @dataclass
            class API:
                """API settings."""
                url: str = "http://localhost"
                timeout: int = 30
            
            api: API | None = None
            
            def __post_init__(self):
                if self.api is None:
                    self.api = self.API()
        
        config = Fuc(GroupedConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        # API fields should be grouped
        lines = content.split('\n')
        api_comment_idx = None
        for i, line in enumerate(lines):
            if "API settings" in line:
                api_comment_idx = i
                break
        
        if api_comment_idx is not None:
            # API fields should come after the comment
            remaining = '\n'.join(lines[api_comment_idx:])
            assert "--api.url" in remaining
            assert "--api.timeout" in remaining


class TestWriteFormattedValues:
    """Test that values are properly formatted when written."""
    
    def test_bool_values_formatted(self, clean_env, tmp_path):
        """Test boolean values formatted as true/false."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--debug", "true"])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        assert "--debug true" in content
    
    def test_string_with_spaces_quoted(self, clean_env, tmp_path):
        """Test strings with spaces are quoted."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "My Application"])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        assert '--name "My Application"' in content
    
    def test_numeric_values_formatted(self, clean_env, tmp_path):
        """Test numeric values are formatted correctly."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--port", "9000"])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        assert "--port 9000" in content


class TestWriteSystemUser:
    """Test write_system and write_user methods."""
    
    def test_write_system_uses_system_path(self, clean_env, tmp_path):
        """Test write_system writes to system path."""
        system_path = tmp_path / "system.fuc"
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--name", "myapp"],
            system_path=str(system_path)
        )
        
        config.write_system()
        
        assert system_path.exists()
        content = system_path.read_text()
        assert "--name myapp" in content
    
    def test_write_user_uses_user_path(self, clean_env, tmp_path):
        """Test write_user writes to user path."""
        user_path = tmp_path / "user.fuc"
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--name", "myapp"],
            user_path=str(user_path)
        )
        
        config.write_user()
        
        assert user_path.exists()
        content = user_path.read_text()
        assert "--name myapp" in content


class TestRoundTrip:
    """Test write then read consistency."""
    
    def test_write_then_read_simple(self, clean_env, tmp_path):
        """Test writing config and reading it back."""
        # Create and write config
        config1 = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--name", "myapp", "--port", "9000", "--debug", "true"]
        )
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        # Read it back
        config2 = Fuc(SimpleConfig, "testapp", cli_args=["--config", str(output_file)])
        
        assert config2.name == "myapp"
        assert config2.port == 9000
        assert config2.debug is True
    
    def test_write_then_read_nested(self, clean_env, tmp_path):
        """Test write/read with nested config."""
        config1 = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--app_name", "myapp", "--server.host", "0.0.0.0", "--server.port", "3000"]
        )
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(NestedConfig, "testapp", cli_args=["--config", str(output_file)])
        
        assert config2.app_name == "myapp"
        assert config2.server.host == "0.0.0.0"
        assert config2.server.port == 3000
    
    def test_write_then_read_lists(self, clean_env, tmp_path):
        """Test write/read with list values."""
        config1 = Fuc(ListConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(ListConfig, "testapp", cli_args=["--config", str(output_file)])
        
        assert config2.names == ["alice", "bob"]
        assert config2.ports == [8080, 8081]
        assert config2.ratios == pytest.approx([0.5, 1.0])


class TestEdgeCases:
    """Test edge cases in writing."""
    
    def test_write_empty_config(self, clean_env, tmp_path):
        """Test writing config with only defaults."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        # Should write all default values
        content = output_file.read_text()
        assert "--name" in content
        assert "--port" in content
        assert "--debug" in content
    
    def test_write_with_special_chars(self, clean_env, tmp_path):
        """Test writing values with special characters."""
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--name", "app@v1.0#test"]
        )
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        # Should be quoted due to special chars
        content = output_file.read_text()
        assert '"app@v1.0#test"' in content or 'app@v1.0#test' in content
    
    def test_write_unicode(self, clean_env, tmp_path):
        """Test writing unicode characters."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "Café"])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        assert "Café" in content
