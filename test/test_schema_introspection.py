"""Tests for schema introspection functionality."""

import pytest
from dataclasses import dataclass
from fuc.types import flatten_schema, get_field_type, validate_key


@dataclass
class SimpleSchema:
    """Simple flat schema."""
    name: str = "default"
    port: int = 8080
    debug: bool = False


@dataclass
class SingleNestedSchema:
    """Schema with one level of nesting."""
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
class DoubleNestedSchema:
    """Schema with two levels of nesting."""
    
    @dataclass
    class Server:
        @dataclass
        class SSL:
            enabled: bool = False
            cert_path: str = "/etc/ssl/cert.pem"
        
        host: str = "localhost"
        port: int = 8000
        ssl: SSL | None = None
        
        def __post_init__(self):
            if self.ssl is None:
                self.ssl = self.SSL()
    
    app_name: str = "myapp"
    server: Server | None = None
    
    def __post_init__(self):
        if self.server is None:
            self.server = self.Server()


@dataclass
class ListSchema:
    """Schema with list fields."""
    names: list[str] | None = None
    ports: list[int] | None = None
    ratios: list[float] | None = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = []
        if self.ports is None:
            self.ports = []
        if self.ratios is None:
            self.ratios = []


class TestFlattenSchema:
    """Test flatten_schema function."""
    
    def test_simple_schema(self):
        """Test flattening simple schema."""
        result = flatten_schema(SimpleSchema)
        assert result == {
            "name": str,
            "port": int,
            "debug": bool,
        }
    
    def test_single_nested_schema(self):
        """Test flattening schema with one level of nesting."""
        result = flatten_schema(SingleNestedSchema)
        assert "app_name" in result
        assert "database.host" in result
        assert "database.port" in result
        assert result["app_name"] == str
        assert result["database.host"] == str
        assert result["database.port"] == int
    
    def test_double_nested_schema(self):
        """Test flattening deeply nested schema."""
        result = flatten_schema(DoubleNestedSchema)
        assert "app_name" in result
        assert "server.host" in result
        assert "server.port" in result
        assert "server.ssl.enabled" in result
        assert "server.ssl.cert_path" in result
        assert result["server.ssl.enabled"] == bool
        assert result["server.ssl.cert_path"] == str
    
    def test_list_schema(self):
        """Test flattening schema with list types."""
        result = flatten_schema(ListSchema)
        assert "names" in result
        assert "ports" in result
        assert "ratios" in result
        # Check that generic types are preserved
        assert result["names"] == list[str]
        assert result["ports"] == list[int]
        assert result["ratios"] == list[float]
    
    def test_empty_schema(self):
        """Test flattening schema with no fields."""
        @dataclass
        class EmptySchema:
            pass
        
        result = flatten_schema(EmptySchema)
        assert result == {}
    
    def test_reserved_key_name_fuc(self):
        """Test that 'fuc' is reserved and raises error."""
        @dataclass
        class InvalidSchema:
            fuc: str = "value"
        
        with pytest.raises(ValueError) as exc_info:
            flatten_schema(InvalidSchema)
        assert "reserved" in str(exc_info.value).lower()
        assert "fuc" in str(exc_info.value)


class TestGetFieldType:
    """Test get_field_type function."""
    
    def test_simple_field_types(self):
        """Test getting types of simple fields."""
        assert get_field_type(SimpleSchema, "name") == str
        assert get_field_type(SimpleSchema, "port") == int
        assert get_field_type(SimpleSchema, "debug") == bool
    
    def test_nested_field_type(self):
        """Test getting type of nested field using dot notation."""
        assert get_field_type(SingleNestedSchema, "database.host") == str
        assert get_field_type(SingleNestedSchema, "database.port") == int
    
    def test_deeply_nested_field_type(self):
        """Test getting type of deeply nested field."""
        result = get_field_type(DoubleNestedSchema, "server.ssl.enabled")
        assert result == bool
        
        result = get_field_type(DoubleNestedSchema, "server.ssl.cert_path")
        assert result == str
    
    def test_list_field_types(self):
        """Test getting generic list types."""
        result = get_field_type(ListSchema, "names")
        assert result == list[str]
        
        result = get_field_type(ListSchema, "ports")
        assert result == list[int]
    
    def test_nonexistent_field(self):
        """Test getting type of nonexistent field raises error."""
        with pytest.raises(AttributeError):
            get_field_type(SimpleSchema, "nonexistent")
    
    def test_nonexistent_nested_field(self):
        """Test getting type of nonexistent nested field raises error."""
        with pytest.raises(AttributeError):
            get_field_type(SingleNestedSchema, "database.nonexistent")
    
    def test_invalid_nesting_path(self):
        """Test invalid nesting path raises error."""
        with pytest.raises(AttributeError):
            get_field_type(SimpleSchema, "name.subfield")


class TestValidateKey:
    """Test validate_key function."""
    
    def test_valid_simple_keys(self):
        """Test validation of simple keys."""
        assert validate_key("name", SimpleSchema) is True
        assert validate_key("port", SimpleSchema) is True
        assert validate_key("debug", SimpleSchema) is True
    
    def test_invalid_simple_key(self):
        """Test validation of invalid simple key."""
        assert validate_key("nonexistent", SimpleSchema) is False
    
    def test_valid_nested_keys(self):
        """Test validation of nested keys."""
        assert validate_key("database.host", SingleNestedSchema) is True
        assert validate_key("database.port", SingleNestedSchema) is True
    
    def test_invalid_nested_key(self):
        """Test validation of invalid nested key."""
        assert validate_key("database.nonexistent", SingleNestedSchema) is False
    
    def test_valid_deeply_nested_keys(self):
        """Test validation of deeply nested keys."""
        assert validate_key("server.ssl.enabled", DoubleNestedSchema) is True
        assert validate_key("server.ssl.cert_path", DoubleNestedSchema) is True
    
    def test_invalid_deeply_nested_key(self):
        """Test validation of invalid deeply nested key."""
        assert validate_key("server.ssl.nonexistent", DoubleNestedSchema) is False
    
    def test_partial_path_to_nested_object(self):
        """Test that partial path to nested object is invalid."""
        # "database" alone is valid (it's a field)
        assert validate_key("database", SingleNestedSchema) is True
        # But trying to access subfield of non-dataclass field should fail
        assert validate_key("name.subfield", SimpleSchema) is False


class TestSchemaWithMixedTypes:
    """Test schema introspection with mixed field types."""
    
    def test_complex_schema(self):
        """Test schema with multiple nested levels and types."""
        @dataclass
        class ComplexSchema:
            version: str = "1.0"
            debug: bool = False
            
            @dataclass
            class API:
                endpoint: str = "http://localhost"
                timeout: float = 30.0
                retries: int = 3
                headers: list[str] | None = None
                
                def __post_init__(self):
                    if self.headers is None:
                        self.headers = []
            
            api: API | None = None
            tags: list[str] | None = None
            
            def __post_init__(self):
                if self.api is None:
                    self.api = self.API()
                if self.tags is None:
                    self.tags = []
        
        # Flatten and check
        flattened = flatten_schema(ComplexSchema)
        assert "version" in flattened
        assert "debug" in flattened
        assert "api.endpoint" in flattened
        assert "api.timeout" in flattened
        assert "api.retries" in flattened
        assert "api.headers" in flattened
        assert "tags" in flattened
        
        # Check types
        assert get_field_type(ComplexSchema, "version") == str
        assert get_field_type(ComplexSchema, "debug") == bool
        assert get_field_type(ComplexSchema, "api.endpoint") == str
        assert get_field_type(ComplexSchema, "api.timeout") == float
        assert get_field_type(ComplexSchema, "api.retries") == int
        assert get_field_type(ComplexSchema, "api.headers") == list[str]
        assert get_field_type(ComplexSchema, "tags") == list[str]
        
        # Validate keys
        assert validate_key("api.timeout", ComplexSchema) is True
        assert validate_key("api.nonexistent", ComplexSchema) is False


class TestEdgeCases:
    """Test edge cases in schema introspection."""
    
    def test_schema_with_optional_fields(self):
        """Test schema with Optional type hints."""
        from typing import Optional
        
        @dataclass
        class OptionalSchema:
            required: str = "default"
            optional: Optional[str] = None
        
        # Optional[str] should still be accessible
        flattened = flatten_schema(OptionalSchema)
        assert "required" in flattened
        assert "optional" in flattened
    
    def test_schema_with_no_defaults(self):
        """Test schema with required fields (no defaults)."""
        @dataclass
        class RequiredSchema:
            name: str
            port: int
        
        flattened = flatten_schema(RequiredSchema)
        assert flattened == {"name": str, "port": int}
        
        assert get_field_type(RequiredSchema, "name") == str
        assert validate_key("name", RequiredSchema) is True
    
    def test_case_sensitivity(self):
        """Test that key validation is case-sensitive."""
        assert validate_key("name", SimpleSchema) is True
        assert validate_key("Name", SimpleSchema) is False
        assert validate_key("NAME", SimpleSchema) is False
    
    def test_underscore_vs_dash_in_names(self):
        """Test field names with underscores."""
        @dataclass
        class UnderscoreSchema:
            app_name: str = "default"
            max_connections: int = 100
        
        assert validate_key("app_name", UnderscoreSchema) is True
        assert validate_key("max_connections", UnderscoreSchema) is True
        # Dashes are not valid Python identifiers
        assert validate_key("app-name", UnderscoreSchema) is False
    
    def test_numeric_in_field_names(self):
        """Test field names with numbers."""
        @dataclass
        class NumericSchema:
            server1: str = "localhost"
            port2: int = 8080
        
        assert validate_key("server1", NumericSchema) is True
        assert validate_key("port2", NumericSchema) is True
    
    def test_flattening_preserves_type_hints(self):
        """Test that generic type hints are preserved."""
        flattened = flatten_schema(ListSchema)
        
        # The types should be the actual generic types, not just list
        names_type = flattened["names"]
        from typing import get_origin, get_args
        assert get_origin(names_type) is list
        assert get_args(names_type) == (str,)
