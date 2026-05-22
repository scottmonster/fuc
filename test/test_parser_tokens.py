"""Tests for token parsing functionality."""

import pytest
from dataclasses import dataclass
from fuc.parser import parse_tokens
from fuc.errors import ParseError, DuplicateKeyError, UnknownKeyError, TypeCastError


@dataclass
class SimpleSchema:
    """Simple schema for testing."""
    name: str = "default"
    port: int = 8080
    debug: bool = False


@dataclass
class NestedSchema:
    """Nested schema for testing dot notation."""
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
class ListSchema:
    """Schema with list fields."""
    names: list[str] | None = None
    ports: list[int] | None = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = []
        if self.ports is None:
            self.ports = []


class TestBasicParsing:
    """Test basic token parsing."""
    
    def test_single_string_value(self):
        """Test parsing single string value."""
        tokens = ["--name", "myapp"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"name": "myapp"}
    
    def test_single_int_value(self):
        """Test parsing single int value."""
        tokens = ["--port", "9000"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"port": 9000}
    
    def test_single_bool_value(self):
        """Test parsing bool value."""
        tokens = ["--debug", "true"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"debug": True}
    
    def test_multiple_key_value_pairs(self):
        """Test parsing multiple key-value pairs."""
        tokens = ["--name", "app", "--port", "3000"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"name": "app", "port": 3000}
    
    def test_all_fields(self):
        """Test parsing all schema fields."""
        tokens = ["--name", "myapp", "--port", "8000", "--debug", "true"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"name": "myapp", "port": 8000, "debug": True}


class TestBooleanFlags:
    """Test boolean flag detection."""
    
    def test_standalone_bool_flag(self):
        """Test standalone boolean flag defaults to True."""
        tokens = ["--debug"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"debug": True}
    
    def test_bool_flag_at_end(self):
        """Test boolean flag at end of tokens."""
        tokens = ["--name", "app", "--debug"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"name": "app", "debug": True}
    
    def test_bool_flag_between_keys(self):
        """Test boolean flag between other keys."""
        tokens = ["--name", "app", "--debug", "--port", "8080"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"name": "app", "debug": True, "port": 8080}
    
    def test_explicit_bool_false(self):
        """Test explicit false value."""
        tokens = ["--debug", "false"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"debug": False}
    
    def test_explicit_bool_true(self):
        """Test explicit true value."""
        tokens = ["--debug", "true"]
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {"debug": True}


class TestNestedKeys:
    """Test parsing with dot notation for nested structures."""
    
    def test_nested_key_string(self):
        """Test nested key with string value."""
        tokens = ["--database.host", "db.example.com"]
        result = parse_tokens(tokens, NestedSchema)
        assert result == {"database": {"host": "db.example.com"}}
    
    def test_nested_key_int(self):
        """Test nested key with int value."""
        tokens = ["--database.port", "3306"]
        result = parse_tokens(tokens, NestedSchema)
        assert result == {"database": {"port": 3306}}
    
    def test_multiple_nested_keys(self):
        """Test multiple nested keys."""
        tokens = ["--database.host", "db.example.com", "--database.port", "3306"]
        result = parse_tokens(tokens, NestedSchema)
        assert result == {"database": {"host": "db.example.com", "port": 3306}}
    
    def test_mixed_nested_and_top_level(self):
        """Test mixing nested and top-level keys."""
        tokens = ["--app_name", "myapp", "--database.host", "localhost"]
        result = parse_tokens(tokens, NestedSchema)
        assert result == {"app_name": "myapp", "database": {"host": "localhost"}}


class TestListValues:
    """Test parsing list values."""
    
    def test_list_of_strings(self):
        """Test parsing list of strings."""
        tokens = ["--names", "alice", "bob", "charlie"]
        result = parse_tokens(tokens, ListSchema)
        assert result == {"names": ["alice", "bob", "charlie"]}
    
    def test_list_of_ints(self):
        """Test parsing list of integers."""
        tokens = ["--ports", "8080", "8081", "8082"]
        result = parse_tokens(tokens, ListSchema)
        assert result == {"ports": [8080, 8081, 8082]}
    
    def test_single_item_list(self):
        """Test list with single item."""
        tokens = ["--names", "alice"]
        result = parse_tokens(tokens, ListSchema)
        assert result == {"names": ["alice"]}


class TestErrorHandling:
    """Test error conditions."""
    
    def test_token_without_dash_prefix(self):
        """Test token without -- prefix raises error."""
        tokens = ["name", "myapp"]
        with pytest.raises(ParseError) as exc_info:
            parse_tokens(tokens, SimpleSchema)
        assert "Expected flag starting with --" in str(exc_info.value)
    
    def test_unknown_key(self):
        """Test unknown key raises UnknownKeyError."""
        tokens = ["--unknown", "value"]
        with pytest.raises(UnknownKeyError) as exc_info:
            parse_tokens(tokens, SimpleSchema)
        assert "unknown" in str(exc_info.value)
    
    def test_duplicate_key(self):
        """Test duplicate key raises DuplicateKeyError."""
        tokens = ["--name", "first", "--name", "second"]
        with pytest.raises(DuplicateKeyError) as exc_info:
            parse_tokens(tokens, SimpleSchema)
        assert "name" in str(exc_info.value)
    
    def test_no_value_for_non_bool(self):
        """Test missing value for non-bool field raises error."""
        tokens = ["--name"]
        with pytest.raises(ParseError) as exc_info:
            parse_tokens(tokens, SimpleSchema)
        assert "No value provided" in str(exc_info.value)
    
    def test_invalid_int_value(self):
        """Test invalid integer value raises TypeCastError."""
        tokens = ["--port", "not_a_number"]
        with pytest.raises(TypeCastError) as exc_info:
            parse_tokens(tokens, SimpleSchema)
        assert "port" in str(exc_info.value)
    
    def test_empty_tokens_list(self):
        """Test empty tokens list returns empty dict."""
        tokens = []
        result = parse_tokens(tokens, SimpleSchema)
        assert result == {}


class TestSourceParameter:
    """Test source parameter for error reporting."""
    
    def test_source_in_parse_error(self):
        """Test source appears in ParseError."""
        tokens = ["invalid"]
        with pytest.raises(ParseError) as exc_info:
            parse_tokens(tokens, SimpleSchema, source="test_file.fuc")
        assert "test_file.fuc" in str(exc_info.value)
    
    def test_source_in_unknown_key_error(self):
        """Test source appears in UnknownKeyError."""
        tokens = ["--invalid", "value"]
        with pytest.raises(UnknownKeyError) as exc_info:
            parse_tokens(tokens, SimpleSchema, source="CLI")
        assert "CLI" in str(exc_info.value)
    
    def test_source_in_duplicate_key_error(self):
        """Test source appears in DuplicateKeyError."""
        tokens = ["--name", "a", "--name", "b"]
        with pytest.raises(DuplicateKeyError) as exc_info:
            parse_tokens(tokens, SimpleSchema, source="environment")
        assert "environment" in str(exc_info.value)


class TestEdgeCases:
    """Test edge cases in token parsing."""
    
    def test_key_with_dash_in_name(self):
        """Test key names can't have dashes (they use underscores)."""
        @dataclass
        class DashSchema:
            app_name: str = "default"
        
        tokens = ["--app_name", "myapp"]
        result = parse_tokens(tokens, DashSchema)
        assert result == {"app_name": "myapp"}
    
    def test_consecutive_bool_flags(self):
        """Test consecutive boolean flags."""
        @dataclass
        class MultiBoolSchema:
            flag1: bool = False
            flag2: bool = False
            flag3: bool = False
        
        tokens = ["--flag1", "--flag2", "--flag3"]
        result = parse_tokens(tokens, MultiBoolSchema)
        assert result == {"flag1": True, "flag2": True, "flag3": True}
    
    def test_value_starting_with_dash(self):
        """Test that values starting with -- are treated as keys."""
        # This should fail because --value looks like a key
        tokens = ["--name", "--value"]
        with pytest.raises(ParseError):
            parse_tokens(tokens, SimpleSchema)
