"""Tests for basic Fuc config class functionality."""

import pytest
import os
from dataclasses import dataclass
from fuc import Fuc
from fuc.config import ConfigProxy


@dataclass
class SimpleConfig:
    """Simple configuration."""
    name: str = "default"
    port: int = 8080
    debug: bool = False


@dataclass
class NestedConfig:
    """Configuration with nesting."""
    app_name: str = "myapp"
    
    @dataclass
    class Database:
        host: str = "localhost"
        port: int = 5432
    
    database: Database | None = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = self.Database()


@dataclass
class ListConfig:
    """Configuration with lists."""
    names: list[str] | None = None
    ports: list[int] | None = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = ["default"]
        if self.ports is None:
            self.ports = [8080]


class TestBasicInitialization:
    """Test basic Fuc initialization."""
    
    def test_minimal_init(self, clean_env):
        """Test minimal initialization with defaults."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        assert config.name == "default"
        assert config.port == 8080
        assert config.debug is False
    
    def test_init_with_nested_config(self, clean_env):
        """Test initialization with nested config."""
        config = Fuc(NestedConfig, "testapp", cli_args=[])
        assert config.app_name == "myapp"
        assert config.database.host == "localhost"
        assert config.database.port == 5432
    
    def test_init_with_list_defaults(self, clean_env):
        """Test initialization with list defaults."""
        config = Fuc(ListConfig, "testapp", cli_args=[])
        assert config.names == ["default"]
        assert config.ports == [8080]
    
    def test_non_dataclass_raises_error(self, clean_env):
        """Test that non-dataclass schema raises error."""
        class NotADataclass:
            pass
        
        with pytest.raises(TypeError) as exc_info:
            Fuc(NotADataclass, "testapp", cli_args=[])
        assert "dataclass" in str(exc_info.value)


class TestAttributeAccess:
    """Test attribute-based configuration access."""
    
    def test_simple_attribute_access(self, clean_env):
        """Test accessing simple attributes."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        assert config.name == "default"
        assert config.port == 8080
        assert config.debug is False
    
    def test_nested_attribute_access(self, clean_env):
        """Test accessing nested attributes."""
        config = Fuc(NestedConfig, "testapp", cli_args=[])
        # Access nested via attribute
        assert config.database.host == "localhost"
        assert config.database.port == 5432
    
    def test_nonexistent_attribute(self, clean_env):
        """Test accessing nonexistent attribute raises error."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        with pytest.raises(AttributeError) as exc_info:
            _ = config.nonexistent
        assert "nonexistent" in str(exc_info.value)
    
    def test_private_attribute_access(self, clean_env):
        """Test accessing private attributes is blocked."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        # Should be able to access actual private attrs through object.__getattribute__
        assert hasattr(config, "_values")
        # But __getattr__ should not expose them
        with pytest.raises(AttributeError):
            config.__getattr__("_values")


class TestConfigProxy:
    """Test ConfigProxy for nested access."""
    
    def test_proxy_wraps_dict(self):
        """Test that ConfigProxy wraps dictionary."""
        data = {"key": "value", "nested": {"inner": "data"}}
        proxy = ConfigProxy(data)
        assert proxy.key == "value"
    
    def test_proxy_nested_access(self):
        """Test proxy provides nested access."""
        data = {"nested": {"inner": "data"}}
        proxy = ConfigProxy(data)
        assert proxy.nested.inner == "data"
    
    def test_proxy_nonexistent_key(self):
        """Test proxy raises AttributeError for nonexistent keys."""
        data = {"key": "value"}
        proxy = ConfigProxy(data)
        with pytest.raises(AttributeError):
            _ = proxy.nonexistent


class TestCLIArgumentParsing:
    """Test CLI argument override."""
    
    def test_cli_overrides_defaults(self, clean_env):
        """Test CLI arguments override defaults."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "customapp"])
        assert config.name == "customapp"
        assert config.port == 8080  # Still default
    
    def test_multiple_cli_args(self, clean_env):
        """Test multiple CLI arguments."""
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--name", "customapp", "--port", "9000", "--debug", "true"]
        )
        assert config.name == "customapp"
        assert config.port == 9000
        assert config.debug is True
    
    def test_nested_cli_args(self, clean_env):
        """Test CLI arguments for nested config."""
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--database.host", "db.example.com", "--database.port", "3306"]
        )
        assert config.database.host == "db.example.com"
        assert config.database.port == 3306


class TestEnvironmentVariables:
    """Test environment variable override."""
    
    def test_env_var_overrides_defaults(self, clean_env, mock_env):
        """Test environment variables override defaults."""
        mock_env({"FUC_TESTAPP_NAME": "envapp"})
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        assert config.name == "envapp"
    
    def test_multiple_env_vars(self, clean_env, mock_env):
        """Test multiple environment variables."""
        mock_env({
            "FUC_TESTAPP_NAME": "envapp",
            "FUC_TESTAPP_PORT": "7000",
            "FUC_TESTAPP_DEBUG": "true"
        })
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        assert config.name == "envapp"
        assert config.port == 7000
        assert config.debug is True
    
    def test_nested_env_vars(self, clean_env, mock_env):
        """Test environment variables for nested config."""
        mock_env({
            "FUC_TESTAPP_DATABASE_HOST": "db.example.com",
            "FUC_TESTAPP_DATABASE_PORT": "3306"
        })
        config = Fuc(NestedConfig, "testapp", cli_args=[])
        assert config.database.host == "db.example.com"
        assert config.database.port == 3306
    
    def test_env_var_name_sanitization(self, clean_env, mock_env):
        """Test app name is sanitized for env vars."""
        # App name with spaces and dashes
        mock_env({"FUC_MY_TEST_APP_NAME": "envapp"})
        config = Fuc(SimpleConfig, "my-test app", cli_args=[])
        assert config.name == "envapp"


class TestFileLoading:
    """Test configuration file loading."""
    
    def test_load_from_cli_config_flag(self, clean_env, tmp_config_file):
        """Test loading from --config flag."""
        config_file = tmp_config_file("--name myapp\n--port 9000")
        config = Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.name == "myapp"
        assert config.port == 9000
    
    def test_cli_args_override_config_file(self, clean_env, tmp_config_file):
        """Test CLI args override config file values."""
        config_file = tmp_config_file("--name myapp\n--port 9000")
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--port", "8000"]
        )
        assert config.name == "myapp"  # From file
        assert config.port == 8000  # From CLI (overrides file)
    
    def test_nonexistent_config_file_ignored(self, clean_env):
        """Test nonexistent config file is silently ignored."""
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=["--config", "/nonexistent/path.fuc"]
        )
        # Should still work with defaults
        assert config.name == "default"


class TestPrecedenceOrder:
    """Test configuration precedence order."""
    
    def test_cli_overrides_env(self, clean_env, mock_env):
        """Test CLI arguments override environment variables."""
        mock_env({"FUC_TESTAPP_NAME": "envapp"})
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "cliapp"])
        assert config.name == "cliapp"
    
    def test_env_overrides_file(self, clean_env, mock_env, tmp_config_file):
        """Test environment variables override config file."""
        config_file = tmp_config_file("--name fileapp")
        mock_env({"FUC_TESTAPP_NAME": "envapp"})
        config = Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.name == "envapp"
    
    def test_file_overrides_defaults(self, clean_env, tmp_config_file):
        """Test config file overrides defaults."""
        config_file = tmp_config_file("--name fileapp")
        config = Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.name == "fileapp"


class TestInternalFucSettings:
    """Test InternalFuc settings."""
    
    def test_custom_paths(self, clean_env):
        """Test custom system and user paths."""
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=[],
            system_path="/custom/system.fuc",
            user_path="/custom/user.fuc"
        )
        assert config.iFuc.system_path == "/custom/system.fuc"
        assert config.iFuc.user_path == "/custom/user.fuc"
    
    def test_custom_env_var(self, clean_env):
        """Test custom environment variable name."""
        config = Fuc(
            SimpleConfig,
            "testapp",
            cli_args=[],
            env_var="CUSTOM_CONFIG_PATH"
        )
        assert config.iFuc.env_var == "CUSTOM_CONFIG_PATH"
    
    def test_default_paths_generated(self, clean_env):
        """Test default paths are generated."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        # Should have non-empty paths
        assert config.iFuc.system_path
        assert config.iFuc.user_path
        assert config.iFuc.env_var
        # Env var should follow pattern
        assert "FUC" in config.iFuc.env_var


class TestSchemaValidation:
    """Test schema is properly used for validation."""
    
    def test_invalid_key_in_cli_raises_error(self, clean_env):
        """Test invalid CLI key raises error."""
        from fuc.errors import UnknownKeyError
        with pytest.raises(UnknownKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--invalid", "value"])
    
    def test_invalid_type_in_cli_raises_error(self, clean_env):
        """Test invalid type in CLI raises error."""
        from fuc.errors import TypeCastError
        with pytest.raises(TypeCastError):
            Fuc(SimpleConfig, "testapp", cli_args=["--port", "not_a_number"])
