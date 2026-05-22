"""Tests for type casting functionality."""

import pytest
from fuc.types import parse_value, _cast_primitive
from fuc.errors import TypeCastError, ParseError


class TestBooleanCasting:
    """Test boolean type casting."""
    
    @pytest.mark.parametrize("value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("Yes", True),
        ("YES", True),
    ])
    def test_true_values(self, value, expected):
        """Test various truthy string representations."""
        result = parse_value([value], bool, "test_key")
        assert result is expected
    
    @pytest.mark.parametrize("value,expected", [
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("No", False),
        ("NO", False),
    ])
    def test_false_values(self, value, expected):
        """Test various falsy string representations."""
        result = parse_value([value], bool, "test_key")
        assert result is expected
    
    def test_invalid_bool_value(self):
        """Test invalid boolean value raises error."""
        with pytest.raises(TypeCastError) as exc_info:
            parse_value(["invalid"], bool, "debug")
        assert "debug" in str(exc_info.value)
    
    def test_bool_with_multiple_values_fails(self):
        """Test boolean with multiple values raises error."""
        with pytest.raises(ParseError):
            parse_value(["true", "false"], bool, "debug")


class TestIntegerCasting:
    """Test integer type casting."""
    
    @pytest.mark.parametrize("value,expected", [
        ("0", 0),
        ("42", 42),
        ("123", 123),
        ("-1", -1),
        ("-100", -100),
        ("999999", 999999),
    ])
    def test_valid_integers(self, value, expected):
        """Test valid integer values."""
        result = parse_value([value], int, "port")
        assert result == expected
        assert isinstance(result, int)
    
    def test_invalid_int_string(self):
        """Test non-numeric string raises error."""
        with pytest.raises(TypeCastError) as exc_info:
            parse_value(["not_a_number"], int, "port")
        assert "port" in str(exc_info.value)
    
    def test_float_string_for_int(self):
        """Test float string for int field raises error."""
        with pytest.raises(TypeCastError):
            parse_value(["3.14"], int, "port")
    
    def test_empty_string(self):
        """Test empty string raises error."""
        with pytest.raises(TypeCastError):
            parse_value([""], int, "port")
    
    def test_int_with_spaces(self):
        """Test integer string with leading/trailing spaces."""
        result = parse_value([" 42 "], int, "port")
        assert result == 42


class TestFloatCasting:
    """Test float type casting."""
    
    @pytest.mark.parametrize("value,expected", [
        ("0.0", 0.0),
        ("3.14", 3.14),
        ("-0.5", -0.5),
        ("1.23456", 1.23456),
        ("42", 42.0),  # Integer string to float
        ("-100.99", -100.99),
    ])
    def test_valid_floats(self, value, expected):
        """Test valid float values."""
        result = parse_value([value], float, "ratio")
        assert result == pytest.approx(expected)
        assert isinstance(result, float)
    
    def test_scientific_notation(self):
        """Test scientific notation."""
        result = parse_value(["1.23e-4"], float, "ratio")
        assert result == pytest.approx(1.23e-4)
    
    def test_invalid_float_string(self):
        """Test non-numeric string raises error."""
        with pytest.raises(TypeCastError):
            parse_value(["not_a_number"], float, "ratio")
    
    def test_float_infinity(self):
        """Test infinity values."""
        result = parse_value(["inf"], float, "ratio")
        assert result == float("inf")
        
        result = parse_value(["-inf"], float, "ratio")
        assert result == float("-inf")


class TestStringCasting:
    """Test string type casting (pass-through)."""
    
    @pytest.mark.parametrize("value", [
        "simple",
        "with spaces",
        "with-dashes",
        "with_underscores",
        "123",
        "true",
        "!@#$%^&*()",
        "",
        "unicode_café_☕",
    ])
    def test_string_values(self, value):
        """Test string values are returned as-is."""
        result = parse_value([value], str, "name")
        assert result == value
        assert isinstance(result, str)


class TestNullNoneCasting:
    """Test null/none value handling."""
    
    @pytest.mark.parametrize("value", [
        "null",
        "Null",
        "NULL",
        "none",
        "None",
        "NONE",
    ])
    def test_null_values(self, value):
        """Test various null/none representations."""
        result = parse_value([value], type(None), "optional_field")
        assert result is None


class TestListStringCasting:
    """Test list[str] type casting."""
    
    def test_single_string(self):
        """Test single string value becomes single-item list."""
        result = parse_value(["alice"], list[str], "names")
        assert result == ["alice"]
    
    def test_multiple_strings(self):
        """Test multiple string values."""
        result = parse_value(["alice", "bob", "charlie"], list[str], "names")
        assert result == ["alice", "bob", "charlie"]
    
    def test_empty_list(self):
        """Test empty values list."""
        result = parse_value([], list[str], "names")
        assert result == []
    
    def test_strings_with_spaces(self):
        """Test strings with spaces (pre-quoted)."""
        result = parse_value(["first name", "second name"], list[str], "names")
        assert result == ["first name", "second name"]


class TestListIntCasting:
    """Test list[int] type casting."""
    
    def test_space_separated_ints(self):
        """Test space-separated integers."""
        result = parse_value(["1 2 3"], list[int], "ports")
        assert result == [1, 2, 3]
    
    def test_comma_separated_ints(self):
        """Test comma-separated integers."""
        result = parse_value(["1,2,3"], list[int], "ports")
        assert result == [1, 2, 3]
    
    def test_comma_and_space_separated(self):
        """Test mixed comma and space separation."""
        result = parse_value(["1, 2, 3"], list[int], "ports")
        assert result == [1, 2, 3]
    
    def test_multiple_token_values(self):
        """Test integers across multiple tokens."""
        result = parse_value(["1", "2", "3"], list[int], "ports")
        assert result == [1, 2, 3]
    
    def test_negative_integers(self):
        """Test negative integers in list."""
        result = parse_value(["-1 -2 -3"], list[int], "offsets")
        assert result == [-1, -2, -3]
    
    def test_single_integer(self):
        """Test single integer in list."""
        result = parse_value(["42"], list[int], "ports")
        assert result == [42]
    
    def test_invalid_int_in_list(self):
        """Test invalid integer in list raises error."""
        with pytest.raises(TypeCastError) as exc_info:
            parse_value(["1 2 invalid"], list[int], "ports")
        assert "ports" in str(exc_info.value)


class TestListFloatCasting:
    """Test list[float] type casting."""
    
    def test_space_separated_floats(self):
        """Test space-separated floats."""
        result = parse_value(["1.1 2.2 3.3"], list[float], "ratios")
        assert result == pytest.approx([1.1, 2.2, 3.3])
    
    def test_comma_separated_floats(self):
        """Test comma-separated floats."""
        result = parse_value(["1.1,2.2,3.3"], list[float], "ratios")
        assert result == pytest.approx([1.1, 2.2, 3.3])
    
    def test_mixed_separation(self):
        """Test mixed comma and space separation."""
        result = parse_value(["1.1, 2.2, 3.3"], list[float], "ratios")
        assert result == pytest.approx([1.1, 2.2, 3.3])
    
    def test_integers_in_float_list(self):
        """Test integers can be parsed as floats."""
        result = parse_value(["1 2 3"], list[float], "ratios")
        assert result == pytest.approx([1.0, 2.0, 3.0])
    
    def test_negative_floats(self):
        """Test negative floats."""
        result = parse_value(["-1.5 -2.5"], list[float], "ratios")
        assert result == pytest.approx([-1.5, -2.5])
    
    def test_invalid_float_in_list(self):
        """Test invalid float in list raises error."""
        with pytest.raises(TypeCastError):
            parse_value(["1.1 invalid"], list[float], "ratios")


class TestPrimitiveCasting:
    """Test _cast_primitive function directly."""
    
    def test_cast_to_int(self):
        """Test casting to int."""
        assert _cast_primitive("42", int) == 42
        assert _cast_primitive("-10", int) == -10
    
    def test_cast_to_float(self):
        """Test casting to float."""
        assert _cast_primitive("3.14", float) == pytest.approx(3.14)
        assert _cast_primitive("-0.5", float) == pytest.approx(-0.5)
    
    def test_cast_to_str(self):
        """Test casting to str."""
        assert _cast_primitive("hello", str) == "hello"
        assert _cast_primitive("123", str) == "123"
    
    def test_unsupported_type(self):
        """Test unsupported type raises error."""
        with pytest.raises(ValueError) as exc_info:
            _cast_primitive("value", dict)
        assert "Unsupported type" in str(exc_info.value)


class TestErrorMessages:
    """Test error messages include proper context."""
    
    def test_type_cast_error_includes_key(self):
        """Test TypeCastError includes the key name."""
        with pytest.raises(TypeCastError) as exc_info:
            parse_value(["invalid"], int, "my_port")
        error = exc_info.value
        assert error.key == "my_port"
        assert "my_port" in str(error)
    
    def test_type_cast_error_includes_expected_type(self):
        """Test TypeCastError includes expected type."""
        with pytest.raises(TypeCastError) as exc_info:
            parse_value(["invalid"], int, "port")
        error = exc_info.value
        assert error.expected == int
        assert "int" in str(error)
    
    def test_type_cast_error_includes_received_value(self):
        """Test TypeCastError includes received value."""
        with pytest.raises(TypeCastError) as exc_info:
            parse_value(["invalid_value"], int, "port")
        error = exc_info.value
        assert error.received == "invalid_value"
        assert "invalid_value" in str(error)


class TestEdgeCases:
    """Test edge cases in type casting."""
    
    def test_zero_values(self):
        """Test zero values for numeric types."""
        assert parse_value(["0"], int, "count") == 0
        assert parse_value(["0.0"], float, "ratio") == pytest.approx(0.0)
    
    def test_boolean_zero_one(self):
        """Test 0 and 1 as boolean values."""
        assert parse_value(["1"], bool, "flag") is True
        assert parse_value(["0"], bool, "flag") is False
    
    def test_whitespace_trimming(self):
        """Test whitespace is handled in numeric values."""
        assert parse_value([" 42 "], int, "port") == 42
        assert parse_value([" 3.14 "], float, "ratio") == pytest.approx(3.14)
    
    def test_very_large_int(self):
        """Test very large integer."""
        large_int = "999999999999999999"
        result = parse_value([large_int], int, "big_number")
        assert result == 999999999999999999
    
    def test_very_small_float(self):
        """Test very small float."""
        result = parse_value(["0.0000000001"], float, "tiny")
        assert result == pytest.approx(0.0000000001)
    
    def test_list_with_empty_strings_filtered(self):
        """Test empty strings in lists are filtered."""
        # Comma-separated with spaces results in empty parts
        result = parse_value(["1,,3"], list[int], "nums")
        # Empty parts are filtered during split
        assert result == [1, 3]
