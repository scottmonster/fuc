"""Tests for provenance tracking integration."""

import pytest
from dataclasses import dataclass
from fuc import Fuc


@dataclass
class TestConfig:
    """Test configuration."""
    value: str = "default"
    port: int = 8080
    debug: bool = False


class TestProvenanceEnabled:
    """Test provenance tracking when enabled."""
    
    def test_track_defaults(self, clean_env):
        """Test provenance tracks default values."""
        config = Fuc(TestConfig, "testapp", cli_args=[], track_provenance=True)
        
        assert hasattr(config, "_provenance")
        assert config._provenance["value"] == "default"
        assert config._provenance["port"] == "default"
        assert config._provenance["debug"] == "default"
    
    def test_track_cli_args(self, clean_env):
        """Test provenance tracks CLI arguments."""
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--value", "cli_value"],
            track_provenance=True
        )
        
        assert config._provenance["value"] == "cli"
        assert config._provenance["port"] == "default"
    
    def test_track_env_vars(self, clean_env, mock_env):
        """Test provenance tracks environment variables."""
        mock_env({"FUC_TESTAPP_VALUE": "env_value"})
        
        config = Fuc(TestConfig, "testapp", cli_args=[], track_provenance=True)
        
        assert config._provenance["value"] == "env"
        assert config._provenance["port"] == "default"
    
    def test_track_config_file(self, clean_env, tmp_path):
        """Test provenance tracks config file source."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--value file_value")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(config_file)],
            track_provenance=True
        )
        
        assert config._provenance["value"] == "cli_config"
        assert config._provenance["port"] == "default"


class TestProvenanceDisabled:
    """Test that provenance is not tracked when disabled."""
    
    def test_no_provenance_by_default(self, clean_env):
        """Test provenance is not tracked by default."""
        config = Fuc(TestConfig, "testapp", cli_args=[])
        
        # _provenance should not exist
        assert not hasattr(config, "_provenance")
    
    def test_no_provenance_when_false(self, clean_env):
        """Test provenance is not tracked when explicitly False."""
        config = Fuc(TestConfig, "testapp", cli_args=[], track_provenance=False)
        
        assert not hasattr(config, "_provenance")


class TestProvenanceSourceNames:
    """Test correct source names in provenance."""
    
    def test_system_config_source(self, clean_env, tmp_path):
        """Test system config source name."""
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system_value")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            system_path=str(system_file),
            track_provenance=True
        )
        
        assert config._provenance["value"] == "system_config"
    
    def test_user_config_source(self, clean_env, tmp_path):
        """Test user config source name."""
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--value user_value")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            user_path=str(user_file),
            track_provenance=True
        )
        
        assert config._provenance["value"] == "user_config"
    
    def test_env_config_source(self, clean_env, tmp_path, mock_env):
        """Test env-selected config source name."""
        env_file = tmp_path / "env.fuc"
        env_file.write_text("--value env_config_value")
        
        mock_env({"FUC_TESTAPP_CONFIG": str(env_file)})
        
        config = Fuc(TestConfig, "testapp", cli_args=[], track_provenance=True)
        
        assert config._provenance["value"] == "env_config"
    
    def test_cli_config_source(self, clean_env, tmp_path):
        """Test CLI-selected config source name."""
        cli_file = tmp_path / "cli.fuc"
        cli_file.write_text("--value cli_config_value")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(cli_file)],
            track_provenance=True
        )
        
        assert config._provenance["value"] == "cli_config"
    
    def test_env_var_source(self, clean_env, mock_env):
        """Test environment variable source name."""
        mock_env({"FUC_TESTAPP_VALUE": "env_value"})
        
        config = Fuc(TestConfig, "testapp", cli_args=[], track_provenance=True)
        
        assert config._provenance["value"] == "env"
    
    def test_cli_arg_source(self, clean_env):
        """Test CLI argument source name."""
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--value", "cli_value"],
            track_provenance=True
        )
        
        assert config._provenance["value"] == "cli"


class TestProvenanceOverrides:
    """Test provenance tracking through overrides."""
    
    def test_provenance_updated_on_override(self, clean_env, tmp_path, mock_env):
        """Test provenance is updated as values are overridden."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--value file_value\n--port 9000")
        
        mock_env({"FUC_TESTAPP_VALUE": "env_value"})
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--value", "cli_value"],
            track_provenance=True
        )
        
        # value overridden multiple times, last one wins
        assert config._provenance["value"] == "cli"
        # port only set in file
        assert config._provenance["port"] == "cli_config"
        # debug never overridden
        assert config._provenance["debug"] == "default"
    
    def test_provenance_tracks_last_source(self, clean_env, tmp_path, mock_env):
        """Test provenance always reflects the last source that set the value."""
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system")
        
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--value user")
        
        mock_env({"FUC_TESTAPP_VALUE": "env"})
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--value", "cli"],
            system_path=str(system_file),
            user_path=str(user_file),
            track_provenance=True
        )
        
        # CLI is the last source
        assert config._provenance["value"] == "cli"


class TestProvenanceNestedConfig:
    """Test provenance with nested configuration."""
    
    def test_nested_provenance_tracking(self, clean_env):
        """Test provenance tracks nested keys."""
        @dataclass
        class NestedConfig:
            @dataclass
            class Database:
                host: str = "localhost"
                port: int = 5432
            
            database: Database | None = None
            
            def __post_init__(self):
                if self.database is None:
                    self.database = self.Database()
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--database.host", "db.example.com"],
            track_provenance=True
        )
        
        assert config._provenance["database.host"] == "cli"
        assert config._provenance["database.port"] == "default"
    
    def test_nested_partial_override_provenance(self, clean_env, tmp_path):
        """Test provenance with partial nested overrides."""
        @dataclass
        class NestedConfig:
            @dataclass
            class Server:
                host: str = "localhost"
                port: int = 8000
            
            server: Server | None = None
            
            def __post_init__(self):
                if self.server is None:
                    self.server = self.Server()
        
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--server.host file_host")
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--server.port", "9000"],
            track_provenance=True
        )
        
        assert config._provenance["server.host"] == "cli_config"
        assert config._provenance["server.port"] == "cli"


class TestProvenanceUseCases:
    """Test practical use cases for provenance."""
    
    def test_debug_config_conflicts(self, clean_env, tmp_path, mock_env):
        """Test using provenance to debug configuration conflicts."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--value file_value\n--port 9000\n--debug false")
        
        mock_env({
            "FUC_TESTAPP_VALUE": "env_value",
            "FUC_TESTAPP_DEBUG": "true"
        })
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--port", "8080"],
            track_provenance=True
        )
        
        # Check where each value came from
        assert config.value == "env_value"
        assert config._provenance["value"] == "env"  # env overrode file
        
        assert config.port == 8080
        assert config._provenance["port"] == "cli"  # CLI overrode file
        
        assert config.debug is True
        assert config._provenance["debug"] == "env"  # env overrode file
    
    def test_verify_source_priority(self, clean_env, tmp_path):
        """Test verifying that correct source won."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--value file")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--value", "cli"],
            track_provenance=True
        )
        
        # Verify CLI won as expected
        assert config.value == "cli"
        assert config._provenance["value"] == "cli"
