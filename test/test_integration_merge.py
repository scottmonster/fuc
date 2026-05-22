"""Tests for nested object deep merging integration."""

import pytest
from dataclasses import dataclass
from fuc import Fuc


@dataclass
class NestedConfig:
    """Config with nested structure."""
    app_name: str = "default"
    
    @dataclass
    class Database:
        host: str = "localhost"
        port: int = 5432
        pool_size: int = 10
    
    @dataclass
    class Cache:
        enabled: bool = False
        ttl: int = 300
    
    database: Database | None = None
    cache: Cache | None = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = self.Database()
        if self.cache is None:
            self.cache = self.Cache()


class TestBasicDeepMerge:
    """Test basic deep merging behavior."""
    
    def test_merge_nested_partial_update(self, clean_env, tmp_path):
        """Test partial updates to nested objects."""
        # First config sets some database values
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--database.host db.example.com")
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        
        # database.host was overridden
        assert config.database.host == "db.example.com"
        # database.port kept default
        assert config.database.port == 5432
        # database.pool_size kept default
        assert config.database.pool_size == 10
    
    def test_merge_multiple_nested_fields(self, clean_env, tmp_path):
        """Test updating multiple fields in nested object."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text(
            "--database.host db.example.com\n"
            "--database.port 3306\n"
        )
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        
        assert config.database.host == "db.example.com"
        assert config.database.port == 3306
        assert config.database.pool_size == 10  # Not specified, kept default
    
    def test_merge_different_nested_objects(self, clean_env):
        """Test merging into different nested objects."""
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=[
                "--database.host", "db.example.com",
                "--cache.enabled", "true",
                "--cache.ttl", "600"
            ]
        )
        
        # database partially updated
        assert config.database.host == "db.example.com"
        assert config.database.port == 5432  # Default
        
        # cache fully updated
        assert config.cache.enabled is True
        assert config.cache.ttl == 600


class TestMultiSourceMerge:
    """Test merging from multiple sources."""
    
    def test_file_then_env_merge(self, clean_env, tmp_path, mock_env):
        """Test file sets some values, env vars set others."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--database.host db.example.com")
        
        mock_env({"FUC_TESTAPP_DATABASE_PORT": "3306"})
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        
        # Both sources contribute
        assert config.database.host == "db.example.com"  # From file
        assert config.database.port == 3306  # From env
        assert config.database.pool_size == 10  # Default
    
    def test_file_env_cli_cascade_merge(self, clean_env, tmp_path, mock_env):
        """Test cascading merge from file -> env -> CLI."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text(
            "--database.host file_host\n"
            "--database.port 5000\n"
            "--database.pool_size 20"
        )
        
        mock_env({
            "FUC_TESTAPP_DATABASE_PORT": "6000"  # Override port from file
        })
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=[
                "--config", str(config_file),
                "--database.pool_size", "30"  # Override pool_size
            ]
        )
        
        # host from file
        assert config.database.host == "file_host"
        # port from env (overrides file)
        assert config.database.port == 6000
        # pool_size from CLI (overrides file and env if present)
        assert config.database.pool_size == 30


class TestOverwriteBehavior:
    """Test that later sources completely overwrite leaf values."""
    
    def test_leaf_value_replaced_not_merged(self, clean_env, tmp_path, mock_env):
        """Test leaf values are replaced, not merged."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--database.host first_host")
        
        mock_env({"FUC_TESTAPP_DATABASE_HOST": "second_host"})
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        
        # Later source (env) completely replaces earlier (file)
        assert config.database.host == "second_host"
    
    def test_cli_completely_overrides(self, clean_env, tmp_path):
        """Test CLI completely overrides file value."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--database.host file_host")
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--database.host", "cli_host"]
        )
        
        assert config.database.host == "cli_host"


class TestListReplacement:
    """Test that list values are replaced, not appended."""
    
    def test_list_replaced_not_appended(self, clean_env, tmp_path):
        """Test list values are completely replaced."""
        @dataclass
        class ListConfig:
            items: list[str] | None = None
            
            def __post_init__(self):
                if self.names is None:
                    self.names = ["default1", "default2"]
        
        config_file = tmp_path / "config.fuc"
        config_file.write_text('--names file1 file2')
        
        config = Fuc(
            ListConfig,
            "testapp",
            cli_args=["--config", str(config_file), "--names", "cli1", "cli2", "cli3"]
        )
        
        # CLI completely replaces file list (not appended)
        assert config.names == ["cli1", "cli2", "cli3"]


class TestDeeplyNestedMerge:
    """Test merging with multiple levels of nesting."""
    
    def test_three_level_nesting(self, clean_env):
        """Test merging with three levels of nesting."""
        @dataclass
        class DeepConfig:
            @dataclass
            class Level1:
                @dataclass
                class Level2:
                    value: str = "default"
                    number: int = 42
                
                level2: Level2 | None = None
                name: str = "level1"
                
                def __post_init__(self):
                    if self.level2 is None:
                        self.level2 = self.Level2()
            
            level1: Level1 | None = None
            
            def __post_init__(self):
                if self.level1 is None:
                    self.level1 = self.Level1()
        
        config = Fuc(
            DeepConfig,
            "testapp",
            cli_args=[
                "--level1.level2.value", "updated",
                "--level1.name", "updated_level1"
            ]
        )
        
        assert config.level1.level2.value == "updated"
        assert config.level1.level2.number == 42  # Default
        assert config.level1.name == "updated_level1"


class TestMergePreservesStructure:
    """Test that merge preserves nested structure."""
    
    def test_nested_dict_structure_preserved(self, clean_env):
        """Test nested dictionary structure is preserved during merge."""
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=[
                "--database.host", "db.example.com",
                "--app_name", "myapp"
            ]
        )
        
        # Both top-level and nested values accessible
        assert config.app_name == "myapp"
        assert config.database.host == "db.example.com"
        assert config.database.port == 5432
        assert config.cache.enabled is False


class TestEmptyMerge:
    """Test merging with empty or no values."""
    
    def test_merge_with_empty_source(self, clean_env, tmp_path):
        """Test merging from empty config file."""
        config_file = tmp_path / "empty.fuc"
        config_file.write_text("")
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        
        # All defaults preserved
        assert config.app_name == "default"
        assert config.database.host == "localhost"
    
    def test_merge_with_comments_only(self, clean_env, tmp_path):
        """Test merging from file with only comments."""
        config_file = tmp_path / "comments.fuc"
        config_file.write_text("# Just comments\n# No actual config")
        
        config = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--config", str(config_file)]
        )
        
        # All defaults preserved
        assert config.app_name == "default"
