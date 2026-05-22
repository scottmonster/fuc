"""Tests for round-trip write/read integration."""

import pytest
from dataclasses import dataclass
from fuc import Fuc


@dataclass
class AllTypesConfig:
    """Config with all supported types."""
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


@dataclass
class NestedConfig:
    """Config with nesting."""
    app_name: str = "myapp"
    
    @dataclass
    class Database:
        host: str = "localhost"
        port: int = 5432
    
    database: Database | None = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = self.Database()


class TestBasicRoundTrip:
    """Test basic write and read back."""
    
    def test_simple_roundtrip(self, clean_env, tmp_path):
        """Test writing and reading simple config."""
        # Create config with custom values
        config1 = Fuc(
            AllTypesConfig,
            "testapp",
            cli_args=["--str_val", "custom", "--int_val", "100"]
        )
        
        # Write to file
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        # Read back
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        
        # Values should match
        assert config2.str_val == "custom"
        assert config2.int_val == 100
        # Defaults preserved for unmodified values
        assert config2.float_val == pytest.approx(3.14)
    
    def test_nested_roundtrip(self, clean_env, tmp_path):
        """Test roundtrip with nested config."""
        config1 = Fuc(
            NestedConfig,
            "testapp",
            cli_args=["--database.host", "db.example.com", "--database.port", "3306"]
        )
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(NestedConfig, "testapp", cli_args=["--config", str(output_file)])
        
        assert config2.database.host == "db.example.com"
        assert config2.database.port == 3306


class TestAllTypesRoundTrip:
    """Test roundtrip for all supported types."""
    
    def test_string_roundtrip(self, clean_env, tmp_path):
        """Test string values roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", "test value"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.str_val == "test value"
    
    def test_int_roundtrip(self, clean_env, tmp_path):
        """Test integer values roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--int_val", "999"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.int_val == 999
    
    def test_float_roundtrip(self, clean_env, tmp_path):
        """Test float values roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--float_val", "2.718"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.float_val == pytest.approx(2.718)
    
    def test_bool_true_roundtrip(self, clean_env, tmp_path):
        """Test boolean true roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--bool_val", "true"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.bool_val is True
    
    def test_bool_false_roundtrip(self, clean_env, tmp_path):
        """Test boolean false roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--bool_val", "false"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.bool_val is False
    
    def test_list_str_roundtrip(self, clean_env, tmp_path):
        """Test list[str] roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--list_str", "x", "y", "z"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.list_str == ["x", "y", "z"]
    
    def test_list_int_roundtrip(self, clean_env, tmp_path):
        """Test list[int] roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--list_int", "10", "20", "30"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.list_int == [10, 20, 30]
    
    def test_list_float_roundtrip(self, clean_env, tmp_path):
        """Test list[float] roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--list_float", "1.5", "2.5", "3.5"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.list_float == pytest.approx([1.5, 2.5, 3.5])


class TestSpecialCharactersRoundTrip:
    """Test roundtrip with special characters."""
    
    def test_spaces_in_string(self, clean_env, tmp_path):
        """Test strings with spaces roundtrip correctly."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", "value with spaces"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.str_val == "value with spaces"
    
    def test_special_chars_in_string(self, clean_env, tmp_path):
        """Test strings with special characters roundtrip."""
        special_value = "value@#$%^&*()!"
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", special_value])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.str_val == special_value
    
    def test_unicode_roundtrip(self, clean_env, tmp_path):
        """Test unicode characters roundtrip."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", "Café ☕"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.str_val == "Café ☕"


class TestDataIntegrity:
    """Test data integrity through roundtrip."""
    
    def test_no_data_loss(self, clean_env, tmp_path):
        """Test no data is lost in roundtrip."""
        # Set all values
        config1 = Fuc(
            AllTypesConfig,
            "testapp",
            cli_args=[
                "--str_val", "custom",
                "--int_val", "100",
                "--float_val", "2.5",
                "--bool_val", "false",
                "--list_str", "a", "b", "c",
                "--list_int", "1", "2", "3",
                "--list_float", "1.1", "2.2", "3.3"
            ]
        )
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        
        # All values should match exactly
        assert config2.str_val == "custom"
        assert config2.int_val == 100
        assert config2.float_val == pytest.approx(2.5)
        assert config2.bool_val is False
        assert config2.list_str == ["a", "b", "c"]
        assert config2.list_int == [1, 2, 3]
        assert config2.list_float == pytest.approx([1.1, 2.2, 3.3])
    
    def test_precision_preserved_float(self, clean_env, tmp_path):
        """Test float precision is preserved."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--float_val", "3.14159265359"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.float_val == pytest.approx(3.14159265359)


class TestMultipleRoundTrips:
    """Test multiple write/read cycles."""
    
    def test_double_roundtrip(self, clean_env, tmp_path):
        """Test writing and reading twice."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", "first"])
        
        file1 = tmp_path / "config1.fuc"
        config1.write(str(file1))
        
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(file1)])
        
        file2 = tmp_path / "config2.fuc"
        config2.write(str(file2))
        
        config3 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(file2)])
        
        assert config3.str_val == "first"
    
    def test_modify_and_roundtrip(self, clean_env, tmp_path):
        """Test reading, modifying via CLI, and writing."""
        # Initial config
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", "initial", "--int_val", "100"])
        
        file1 = tmp_path / "config1.fuc"
        config1.write(str(file1))
        
        # Read and modify
        config2 = Fuc(
            AllTypesConfig,
            "testapp",
            cli_args=["--config", str(file1), "--int_val", "200"]  # Override int_val
        )
        
        file2 = tmp_path / "config2.fuc"
        config2.write(str(file2))
        
        # Read final config
        config3 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(file2)])
        
        assert config3.str_val == "initial"  # Preserved
        assert config3.int_val == 200  # Modified


class TestFormatPreservation:
    """Test that file format is preserved."""
    
    def test_file_is_valid_fuc_format(self, clean_env, tmp_path):
        """Test written file is valid .fuc format."""
        config1 = Fuc(AllTypesConfig, "testapp", cli_args=["--str_val", "test"])
        
        output_file = tmp_path / "config.fuc"
        config1.write(str(output_file))
        
        # Read file as text
        content = output_file.read_text()
        
        # Should contain --key value format
        assert "--str_val" in content
        # Should be readable by parser
        config2 = Fuc(AllTypesConfig, "testapp", cli_args=["--config", str(output_file)])
        assert config2.str_val == "test"
    
    def test_comments_present_in_written_file(self, clean_env, tmp_path):
        """Test comments (docstrings) are present in written file."""
        config = Fuc(AllTypesConfig, "testapp", cli_args=[])
        
        output_file = tmp_path / "config.fuc"
        config.write(str(output_file))
        
        content = output_file.read_text()
        # Should have comments
        assert "#" in content
