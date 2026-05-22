"""Tests for value formatting functionality."""

import pytest
from fuc.parser import format_value
from typing import get_origin


class TestStringFormatting:
    """Test string value formatting."""
    
    def test_simple_string(self):
        """Test simple string without special characters."""
        result = format_value("myapp", str)
        assert result == "myapp"
    
    def test_string_with_spaces(self):
        """Test string with spaces gets quoted."""
        result = format_value("My Application", str)
        assert result == '"My Application"'
    
    def test_string_with_double_quotes(self):
        """Test string with double quotes gets escaped."""
        result = format_value('Say "hello"', str)
        assert result == '"Say \\"hello\\""'
    
    def test_string_with_special_chars(self):
        """Test string with special characters gets quoted."""
        special_chars = ['#', '$', '&', '|', ';', '<', '>', '(', ')', 
                        '[', ']', '{', '}', '*', '?', '~', '`']
        
        for char in special_chars:
            result = format_value(f"value{char}test", str)
            assert result.startswith('"') and result.endswith('"')
    
    def test_empty_string(self):
        """Test empty string."""
        result = format_value("", str)
        assert result == ""
    
    def test_string_with_backslash(self):
        """Test string with backslash."""
        result = format_value("path\\to\\file", str)
        assert result == '"path\\to\\file"'


class TestBooleanFormatting:
    """Test boolean value formatting."""
    
    def test_true_value(self):
        """Test True formats to 'true'."""
        result = format_value(True, bool)
        assert result == "true"
    
    def test_false_value(self):
        """Test False formats to 'false'."""
        result = format_value(False, bool)
        assert result == "false"


class TestNumericFormatting:
    """Test numeric value formatting."""
    
    def test_positive_int(self):
        """Test positive integer."""
        result = format_value(42, int)
        assert result == "42"
    
    def test_negative_int(self):
        """Test negative integer."""
        result = format_value(-100, int)
        assert result == "-100"
    
    def test_zero(self):
        """Test zero."""
        result = format_value(0, int)
        assert result == "0"
    
    def test_positive_float(self):
        """Test positive float."""
        result = format_value(3.14, float)
        assert result == "3.14"
    
    def test_negative_float(self):
        """Test negative float."""
        result = format_value(-0.5, float)
        assert result == "-0.5"
    
    def test_float_with_many_decimals(self):
        """Test float with many decimal places."""
        result = format_value(3.14159265359, float)
        assert result == "3.14159265359"


class TestNullFormatting:
    """Test null/None value formatting."""
    
    def test_none_value(self):
        """Test None formats to 'null'."""
        result = format_value(None, type(None))
        assert result == "null"


class TestListFormatting:
    """Test list value formatting."""
    
    def test_list_of_strings(self):
        """Test list[str] formats with quoted items."""
        result = format_value(["alice", "bob", "charlie"], list[str])
        assert result == '"alice" "bob" "charlie"'
    
    def test_list_of_ints(self):
        """Test list[int] formats with space-separated values."""
        result = format_value([1, 2, 3], list[int])
        assert result == "1 2 3"
    
    def test_list_of_floats(self):
        """Test list[float] formats with space-separated values."""
        result = format_value([1.1, 2.2, 3.3], list[float])
        assert result == "1.1 2.2 3.3"
    
    def test_single_item_list_str(self):
        """Test single-item string list."""
        result = format_value(["only"], list[str])
        assert result == '"only"'
    
    def test_single_item_list_int(self):
        """Test single-item integer list."""
        result = format_value([42], list[int])
        assert result == "42"
    
    def test_empty_list(self):
        """Test empty list."""
        result = format_value([], list[str])
        assert result == ""
    
    def test_list_with_strings_containing_spaces(self):
        """Test list of strings where items have spaces."""
        result = format_value(["first value", "second value"], list[str])
        assert result == '"first value" "second value"'


class TestRoundTripConsistency:
    """Test that formatted values can be parsed back."""
    
    def test_string_round_trip(self):
        """Test string formatting is parse-compatible."""
        from fuc.parser import tokenize_line
        
        formatted = format_value("my app", str)
        tokens = tokenize_line(f"--name {formatted}")
        assert tokens == ["--name", "my app"]
    
    def test_bool_round_trip(self):
        """Test bool formatting is parse-compatible."""
        from fuc.parser import tokenize_line
        from fuc.types import parse_value
        
        formatted = format_value(True, bool)
        parsed = parse_value([formatted], bool, "test")
        assert parsed is True
        
        formatted = format_value(False, bool)
        parsed = parse_value([formatted], bool, "test")
        assert parsed is False
    
    def test_int_round_trip(self):
        """Test int formatting is parse-compatible."""
        from fuc.types import parse_value
        
        formatted = format_value(42, int)
        parsed = parse_value([formatted], int, "test")
        assert parsed == 42
    
    def test_float_round_trip(self):
        """Test float formatting is parse-compatible."""
        from fuc.types import parse_value
        
        formatted = format_value(3.14, float)
        parsed = parse_value([formatted], float, "test")
        assert parsed == 3.14
    
    def test_list_int_round_trip(self):
        """Test list[int] formatting is parse-compatible."""
        from fuc.parser import tokenize_line
        from fuc.types import parse_value
        
        formatted = format_value([1, 2, 3], list[int])
        tokens = tokenize_line(f"--ports {formatted}")
        # Remove --ports key
        value_tokens = tokens[1:]
        parsed = parse_value(value_tokens, list[int], "test")
        assert parsed == [1, 2, 3]
    
    def test_list_str_round_trip(self):
        """Test list[str] formatting is parse-compatible."""
        from fuc.parser import tokenize_line
        from fuc.types import parse_value
        
        formatted = format_value(["alice", "bob"], list[str])
        tokens = tokenize_line(f"--names {formatted}")
        # Remove --names key
        value_tokens = tokens[1:]
        parsed = parse_value(value_tokens, list[str], "test")
        assert parsed == ["alice", "bob"]


class TestEdgeCases:
    """Test edge cases in formatting."""
    
    def test_string_with_newline_chars(self):
        """Test string containing newline escape sequence."""
        result = format_value("line1\\nline2", str)
        # Should be quoted because of backslash
        assert result == '"line1\\nline2"'
    
    def test_string_with_tabs(self):
        """Test string with tab characters."""
        result = format_value("value\twith\ttabs", str)
        assert result.startswith('"') and result.endswith('"')
    
    def test_very_long_string(self):
        """Test very long string."""
        long_str = "a" * 1000
        result = format_value(long_str, str)
        # Simple string without special chars shouldn't be quoted
        assert result == long_str
    
    def test_very_long_list(self):
        """Test very long list."""
        long_list = list(range(100))
        result = format_value(long_list, list[int])
        # Should have 100 space-separated numbers
        parts = result.split()
        assert len(parts) == 100
        assert parts[0] == "0"
        assert parts[99] == "99"
    
    def test_unicode_string(self):
        """Test unicode characters in string."""
        result = format_value("Café ☕", str)
        # Contains space, so should be quoted
        assert result == '"Café ☕"'
    
    def test_path_like_strings(self):
        """Test path-like strings."""
        # Unix path
        result = format_value("/home/user/config.fuc", str)
        assert result == "/home/user/config.fuc"
        
        # Path with spaces
        result = format_value("/home/user/my config/app.fuc", str)
        assert result == '"/home/user/my config/app.fuc"'
    
    def test_url_string(self):
        """Test URL strings."""
        result = format_value("http://example.com:8080", str)
        # Colon is a special char
        assert result == '"http://example.com:8080"'
    
    def test_negative_numbers_in_list(self):
        """Test negative numbers in list."""
        result = format_value([-1, -2, -3], list[int])
        assert result == "-1 -2 -3"
