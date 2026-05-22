"""Tests for edge cases and boundary conditions."""

import pytest
import os
from dataclasses import dataclass
from fuc import Fuc
from fuc.errors import DuplicateKeyError, UnknownKeyError


@dataclass
class SimpleConfig:
    """Simple config for edge case testing."""
    name: str = "default"
    count: int = 0
    items: list[str] | None = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []


class TestDuplicateKeys:
    """Test handling of duplicate key definitions."""
    
    def test_duplicate_keys_in_file(self, tmp_path, clean_env):
        """Test duplicate keys in file raises error."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--name first\n--name second\n")
        
        with pytest.raises(DuplicateKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_duplicate_keys_in_cli(self, clean_env):
        """Test duplicate keys in CLI - last one wins."""
        # CLI allows overrides, so last wins
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "first", "--name", "second"])
        assert config.name == "second"
    
    def test_duplicate_nested_keys(self, tmp_path, clean_env):
        """Test duplicate nested keys in file."""
        @dataclass
        class NestedConfig:
            @dataclass
            class Database:
                host: str = "localhost"
            
            database: Database | None = None
            
            def __post_init__(self):
                if self.database is None:
                    self.database = self.Database()
        
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--database.host first\n--database.host second\n")
        
        with pytest.raises(DuplicateKeyError):
            Fuc(NestedConfig, "testapp", cli_args=["--config", str(config_file)])


class TestUnknownKeys:
    """Test handling of unknown keys."""
    
    def test_unknown_key_in_file(self, tmp_path, clean_env):
        """Test unknown key in file raises error."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--unknown value\n")
        
        with pytest.raises(UnknownKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
    
    def test_unknown_key_in_cli(self, clean_env):
        """Test unknown key in CLI raises error."""
        with pytest.raises(UnknownKeyError):
            Fuc(SimpleConfig, "testapp", cli_args=["--invalid", "value"])
    
    def test_unknown_nested_key(self, clean_env):
        """Test unknown nested key raises error."""
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
            Fuc(NestedConfig, "testapp", cli_args=["--database.unknown", "value"])


class TestEmptyValues:
    """Test handling of empty values."""
    
    def test_empty_string(self, clean_env):
        """Test empty string values."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", ""])
        assert config.name == ""
    
    def test_empty_list(self, clean_env):
        """Test empty list default."""
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        assert config.items == []
    
    def test_empty_list_explicit(self, tmp_path, clean_env):
        """Test explicitly setting empty list."""
        config_file = tmp_path / "config.fuc"
        # No items specified means default empty list
        config_file.write_text("--name test\n")
        
        config = Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.items == []


class TestSpecialCharacters:
    """Test handling of special characters."""
    
    def test_special_chars_in_value(self, clean_env):
        """Test special characters in string values."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "test@#$%^&*()"])
        assert config.name == "test@#$%^&*()"
    
    def test_equals_sign_in_value(self, clean_env):
        """Test equals sign in values."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "key=value"])
        assert config.name == "key=value"
    
    def test_quotes_in_value(self, tmp_path, clean_env):
        """Test quotes in values."""
        config_file = tmp_path / "config.fuc"
        config_file.write_text('--name "quoted value"\n')
        
        config = Fuc(SimpleConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.name == "quoted value"
    
    def test_unicode_characters(self, clean_env):
        """Test unicode characters in values."""
        config = Fuc(SimpleConfig, "testapp", cli_args=["--name", "Café ☕ 中文"])
        assert config.name == "Café ☕ 中文"


class TestPathsWithSpaces:
    """Test handling of paths with spaces."""
    
    def test_path_with_spaces_unquoted(self, clean_env):
        """Test path with spaces unquoted in CLI."""
        @dataclass
        class PathConfig:
            path: str = "/default"
        
        # CLI requires quoting or escaping for spaces
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "/my path/file"])
        assert config.path == "/my path/file"
    
    def test_path_with_spaces_quoted(self, tmp_path, clean_env):
        """Test path with spaces quoted in file."""
        @dataclass
        class PathConfig:
            path: str = "/default"
        
        config_file = tmp_path / "config.fuc"
        config_file.write_text('--path "/my path/file"\n')
        
        config = Fuc(PathConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.path == "/my path/file"


class TestNumericEdgeCases:
    """Test numeric edge cases."""
    
    def test_int_max_value(self, clean_env):
        """Test large integer values."""
        @dataclass
        class IntConfig:
            value: int = 0
        
        config = Fuc(IntConfig, "testapp", cli_args=["--value", "2147483647"])
        assert config.value == 2147483647
    
    def test_int_negative(self, clean_env):
        """Test negative integer values."""
        @dataclass
        class IntConfig:
            value: int = 0
        
        config = Fuc(IntConfig, "testapp", cli_args=["--value", "-999"])
        assert config.value == -999
    
    def test_float_scientific_notation(self, clean_env):
        """Test float scientific notation."""
        @dataclass
        class FloatConfig:
            value: float = 0.0
        
        config = Fuc(FloatConfig, "testapp", cli_args=["--value", "1.5e10"])
        assert config.value == pytest.approx(1.5e10)
    
    def test_float_negative(self, clean_env):
        """Test negative float values."""
        @dataclass
        class FloatConfig:
            value: float = 0.0
        
        config = Fuc(FloatConfig, "testapp", cli_args=["--value", "-3.14"])
        assert config.value == pytest.approx(-3.14)


class TestDeeplyNestedConfigs:
    """Test deeply nested configuration structures."""
    
    def test_three_level_nesting(self, clean_env):
        """Test three levels of nesting."""
        @dataclass
        class DeepConfig:
            @dataclass
            class Level1:
                @dataclass
                class Level2:
                    value: str = "deep"
                
                level2: Level2 | None = None
                
                def __post_init__(self):
                    if self.level2 is None:
                        self.level2 = self.Level2()
            
            level1: Level1 | None = None
            
            def __post_init__(self):
                if self.level1 is None:
                    self.level1 = self.Level1()
        
        config = Fuc(DeepConfig, "testapp", cli_args=["--level1.level2.value", "test"])
        assert config.level1.level2.value == "test"


class TestEnvironmentVariableNames:
    """Test environment variable name sanitization."""
    
    def test_env_var_spaces_to_underscores(self, clean_env):
        """Test spaces in key names convert to underscores in env vars."""
        @dataclass
        class SpaceConfig:
            app_name: str = "default"
        
        os.environ["TESTAPP_APP_NAME"] = "from_env"
        
        config = Fuc(SpaceConfig, "testapp", cli_args=[])
        assert config.app_name == "from_env"
        
        del os.environ["TESTAPP_APP_NAME"]
    
    def test_env_var_uppercase(self, clean_env):
        """Test env vars are uppercase."""
        @dataclass
        class CaseConfig:
            my_value: str = "default"
        
        os.environ["TESTAPP_MY_VALUE"] = "from_env"
        
        config = Fuc(CaseConfig, "testapp", cli_args=[])
        assert config.my_value == "from_env"
        
        del os.environ["TESTAPP_MY_VALUE"]


class TestEmptySchema:
    """Test behavior with empty or minimal schemas."""
    
    def test_schema_with_no_fields(self, clean_env):
        """Test dataclass with no custom fields."""
        @dataclass
        class EmptyConfig:
            pass
        
        # Should not crash
        config = Fuc(EmptyConfig, "testapp", cli_args=[])
        assert isinstance(config, EmptyConfig)
    
    def test_schema_with_only_defaults(self, clean_env):
        """Test schema where all fields have defaults."""
        @dataclass
        class DefaultsConfig:
            a: str = "a"
            b: int = 1
            c: bool = True
        
        # Should use defaults
        config = Fuc(DefaultsConfig, "testapp", cli_args=[])
        assert config.a == "a"
        assert config.b == 1
        assert config.c is True


class TestBooleanEdgeCases:
    """Test boolean flag edge cases."""
    
    def test_bool_flag_no_value(self, tmp_path, clean_env):
        """Test boolean flags without values default to true."""
        @dataclass
        class BoolConfig:
            enabled: bool = False
        
        config_file = tmp_path / "config.fuc"
        config_file.write_text("--enabled\n")
        
        config = Fuc(BoolConfig, "testapp", cli_args=["--config", str(config_file)])
        assert config.enabled is True
    
    def test_multiple_bool_representations(self, clean_env):
        """Test various boolean representations."""
        @dataclass
        class BoolConfig:
            flag: bool = False
        
        # Test true variations
        for value in ["true", "True", "TRUE", "1", "yes", "Yes"]:
            config = Fuc(BoolConfig, "testapp", cli_args=["--flag", value])
            assert config.flag is True, f"Failed for {value}"
        
        # Test false variations
        for value in ["false", "False", "FALSE", "0", "no", "No"]:
            config = Fuc(BoolConfig, "testapp", cli_args=["--flag", value])
            assert config.flag is False, f"Failed for {value}"
