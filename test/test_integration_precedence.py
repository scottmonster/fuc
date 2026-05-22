"""Tests for full precedence chain integration."""

import pytest
import os
from pathlib import Path
from dataclasses import dataclass
from fuc import Fuc


@dataclass
class TestConfig:
    """Test configuration."""
    value: str = "default"
    port: int = 8080


class TestFullPrecedenceChain:
    """Test all 8 levels of precedence."""
    
    def test_defaults_only(self, clean_env):
        """Test Level 1: Built-in defaults."""
        config = Fuc(TestConfig, "testapp", cli_args=[])
        assert config.value == "default"
        assert config.port == 8080
    
    def test_system_config_overrides_defaults(self, clean_env, tmp_path, monkeypatch):
        """Test Level 2: System config overrides defaults."""
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system\n--port 9000")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            system_path=str(system_file)
        )
        assert config.value == "system"
        assert config.port == 9000
    
    def test_user_config_overrides_system(self, clean_env, tmp_path):
        """Test Level 3: User config overrides system config."""
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system")
        
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--value user")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            system_path=str(system_file),
            user_path=str(user_file)
        )
        assert config.value == "user"
    
    def test_env_config_overrides_user(self, clean_env, tmp_path, mock_env):
        """Test Level 4: Env-selected config overrides user config."""
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--value user")
        
        env_file = tmp_path / "env.fuc"
        env_file.write_text("--value env_config")
        
        # Set environment variable for config path
        mock_env({"FUC_TESTAPP_CONFIG": str(env_file)})
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            user_path=str(user_file)
        )
        assert config.value == "env_config"
    
    def test_cli_config_overrides_env_config(self, clean_env, tmp_path, mock_env):
        """Test Level 5: CLI-selected config overrides env-selected config."""
        env_file = tmp_path / "env.fuc"
        env_file.write_text("--value env_config")
        
        cli_file = tmp_path / "cli.fuc"
        cli_file.write_text("--value cli_config")
        
        mock_env({"FUC_TESTAPP_CONFIG": str(env_file)})
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(cli_file)]
        )
        assert config.value == "cli_config"
    
    def test_env_vars_override_cli_config(self, clean_env, tmp_path, mock_env):
        """Test Level 6: Environment variables override CLI-selected config."""
        cli_file = tmp_path / "cli.fuc"
        cli_file.write_text("--value cli_config")
        
        mock_env({"FUC_TESTAPP_VALUE": "env_var"})
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(cli_file)]
        )
        assert config.value == "env_var"
    
    def test_cli_args_override_env_vars(self, clean_env, mock_env):
        """Test Level 7: CLI arguments override environment variables."""
        mock_env({"FUC_TESTAPP_VALUE": "env_var"})
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--value", "cli_arg"]
        )
        assert config.value == "cli_arg"
    
    def test_full_chain_cli_wins(self, clean_env, tmp_path, mock_env):
        """Test full precedence chain with CLI winning."""
        # Set up all levels
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system\n--port 1000")
        
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--value user\n--port 2000")
        
        env_config_file = tmp_path / "env_config.fuc"
        env_config_file.write_text("--value env_config\n--port 3000")
        
        cli_config_file = tmp_path / "cli_config.fuc"
        cli_config_file.write_text("--value cli_config\n--port 4000")
        
        # Set environment
        mock_env({
            "FUC_TESTAPP_CONFIG": str(env_config_file),
            "FUC_TESTAPP_VALUE": "env_var",
            "FUC_TESTAPP_PORT": "5000"
        })
        
        # CLI args have highest priority
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(cli_config_file), "--value", "cli_arg", "--port", "6000"],
            system_path=str(system_file),
            user_path=str(user_file)
        )
        
        assert config.value == "cli_arg"
        assert config.port == 6000


class TestPartialOverrides:
    """Test that later sources only override specified values."""
    
    def test_file_partial_override(self, clean_env, tmp_path):
        """Test file only overrides specified values."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--value override")
        # Note: port not specified
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        assert config.value == "override"
        assert config.port == 8080  # Still default
    
    def test_env_partial_override(self, clean_env, mock_env):
        """Test environment variable only overrides specified values."""
        mock_env({"FUC_TESTAPP_VALUE": "env_value"})
        # No env var for port
        
        config = Fuc(TestConfig, "testapp", cli_args=[])
        assert config.value == "env_value"
        assert config.port == 8080  # Still default
    
    def test_cli_partial_override(self, clean_env):
        """Test CLI only overrides specified values."""
        config = Fuc(TestConfig, "testapp", cli_args=["--value", "cli_value"])
        assert config.value == "cli_value"
        assert config.port == 8080  # Still default


class TestMissingFilesIgnored:
    """Test that missing config files are silently ignored."""
    
    def test_missing_system_config_ignored(self, clean_env):
        """Test missing system config doesn't cause error."""
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            system_path="/nonexistent/system.fuc"
        )
        # Should fall back to defaults
        assert config.value == "default"
    
    def test_missing_user_config_ignored(self, clean_env):
        """Test missing user config doesn't cause error."""
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            user_path="/nonexistent/user.fuc"
        )
        assert config.value == "default"
    
    def test_missing_env_config_ignored(self, clean_env, mock_env):
        """Test missing env-selected config doesn't cause error."""
        mock_env({"FUC_TESTAPP_CONFIG": "/nonexistent/env.fuc"})
        
        config = Fuc(TestConfig, "testapp", cli_args=[])
        assert config.value == "default"
    
    def test_missing_cli_config_ignored(self, clean_env):
        """Test missing CLI-selected config doesn't cause error."""
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", "/nonexistent/cli.fuc"]
        )
        assert config.value == "default"


class TestInvalidFilesSilentlySkipped:
    """Test that files with errors are silently skipped."""
    
    def test_invalid_system_config_skipped(self, clean_env, tmp_path):
        """Test system config with errors is skipped."""
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--invalid_key value")
        
        # Should not raise error, just skip the file
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            system_path=str(system_file)
        )
        assert config.value == "default"
    
    def test_invalid_user_config_skipped(self, clean_env, tmp_path):
        """Test user config with errors is skipped."""
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--port not_a_number")
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=[],
            user_path=str(user_file)
        )
        assert config.port == 8080  # Default, not from invalid file


class TestConfigOverrideCombinations:
    """Test various combinations of override sources."""
    
    def test_file_and_env_and_cli(self, clean_env, tmp_path, mock_env):
        """Test combining file, env var, and CLI arg."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--value file\n--port 9000")
        
        mock_env({"FUC_TESTAPP_VALUE": "env"})
        
        # CLI overrides env which overrides file
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--value", "cli"]
        )
        
        assert config.value == "cli"  # CLI wins
        assert config.port == 9000  # From file (not overridden)
    
    def test_system_user_and_cli_config(self, clean_env, tmp_path):
        """Test system, user, and CLI config files."""
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system\n--port 1000")
        
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--port 2000")  # Override port only
        
        cli_config_file = tmp_path / "cli.fuc"
        cli_config_file.write_text("--port 3000")  # Override port again
        
        config = Fuc(
            TestConfig,
            "testapp",
            cli_args=["--config", str(cli_config_file)],
            system_path=str(system_file),
            user_path=str(user_file)
        )
        
        # value from system (not overridden by user or cli config)
        assert config.value == "system"
        # port from CLI config (latest)
        assert config.port == 3000
