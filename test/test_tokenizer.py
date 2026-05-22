"""Tests for tokenizer functionality."""

import pytest
from fuc.parser import tokenize_line


class TestBasicTokenization:
    """Test basic tokenization without quotes."""
    
    def test_simple_key_value(self):
        """Test simple --key value pattern."""
        result = tokenize_line("--name myapp")
        assert result == ["--name", "myapp"]
    
    def test_multiple_key_value_pairs(self):
        """Test multiple key-value pairs."""
        result = tokenize_line("--name app --port 8080")
        assert result == ["--name", "app", "--port", "8080"]
    
    def test_key_with_multiple_values(self):
        """Test key with multiple values."""
        result = tokenize_line("--servers a b c")
        assert result == ["--servers", "a", "b", "c"]
    
    def test_empty_line(self):
        """Test empty line returns empty list."""
        result = tokenize_line("")
        assert result == []
    
    def test_whitespace_only(self):
        """Test line with only whitespace."""
        result = tokenize_line("   \t  ")
        assert result == []


class TestDoubleQuotes:
    """Test tokenization with double quotes."""
    
    def test_double_quoted_value(self):
        """Test value in double quotes."""
        result = tokenize_line('--name "Bane Joe"')
        assert result == ["--name", "Bane Joe"]
    
    def test_multiple_double_quoted_values(self):
        """Test multiple double-quoted values."""
        result = tokenize_line('--servers "alpha" "beta" "gamma"')
        assert result == ["--servers", "alpha", "beta", "gamma"]
    
    def test_double_quotes_with_special_chars(self):
        """Test double quotes with special characters."""
        result = tokenize_line('--message "Hello, World! @#$%"')
        assert result == ["--message", "Hello, World! @#$%"]
    
    def test_double_quotes_preserve_whitespace(self):
        """Test that double quotes preserve internal whitespace."""
        result = tokenize_line('--text "  multiple   spaces  "')
        assert result == ["--text", "  multiple   spaces  "]
    
    def test_empty_double_quoted_string(self):
        """Test empty double-quoted string."""
        result = tokenize_line('--name ""')
        assert result == ["--name"]


class TestSingleQuotes:
    """Test tokenization with single quotes."""
    
    def test_single_quoted_value(self):
        """Test value in single quotes."""
        result = tokenize_line("--name 'Bane Joe'")
        assert result == ["--name", "Bane Joe"]
    
    def test_multiple_single_quoted_values(self):
        """Test multiple single-quoted values."""
        result = tokenize_line("--servers 'alpha' 'beta' 'gamma'")
        assert result == ["--servers", "alpha", "beta", "gamma"]
    
    def test_single_quotes_preserve_whitespace(self):
        """Test that single quotes preserve internal whitespace."""
        result = tokenize_line("--text '  multiple   spaces  '")
        assert result == ["--text", "  multiple   spaces  "]
    
    def test_empty_single_quoted_string(self):
        """Test empty single-quoted string."""
        result = tokenize_line("--name ''")
        assert result == ["--name"]


class TestMixedQuotes:
    """Test tokenization with mixed quote types."""
    
    def test_mixed_double_and_single(self):
        """Test mixing double and single quotes in same line."""
        result = tokenize_line('--a "double" --b \'single\'')
        assert result == ["--a", "double", "--b", "single"]
    
    def test_single_quotes_inside_double(self):
        """Test single quotes inside double quotes."""
        result = tokenize_line('--text "It\'s working"')
        assert result == ["--text", "It's working"]
    
    def test_double_quotes_inside_single(self):
        """Test double quotes inside single quotes."""
        result = tokenize_line('--text \'Say "hello"\'')
        assert result == ["--text", 'Say "hello"']


class TestPathsWithSpaces:
    """Test handling of file paths with spaces."""
    
    def test_path_with_spaces_double_quoted(self):
        """Test file path with spaces in double quotes."""
        result = tokenize_line('--config "/home/user/my config/app.fuc"')
        assert result == ["--config", "/home/user/my config/app.fuc"]
    
    def test_path_with_spaces_single_quoted(self):
        """Test file path with spaces in single quotes."""
        result = tokenize_line("--config '/home/user/my config/app.fuc'")
        assert result == ["--config", "/home/user/my config/app.fuc"]
    
    def test_windows_path_with_spaces(self):
        """Test Windows path with spaces."""
        result = tokenize_line('--config "C:\\Program Files\\MyApp\\config.fuc"')
        assert result == ["--config", "C:\\Program Files\\MyApp\\config.fuc"]


class TestSpecialCharacters:
    """Test handling of special characters."""
    
    def test_equals_sign(self):
        """Test equals sign in value."""
        result = tokenize_line('--formula "a=b+c"')
        assert result == ["--formula", "a=b+c"]
    
    def test_colons(self):
        """Test colons in value."""
        result = tokenize_line('--url "http://example.com:8080"')
        assert result == ["--url", "http://example.com:8080"]
    
    def test_brackets(self):
        """Test brackets in value."""
        result = tokenize_line('--data "[1,2,3]"')
        assert result == ["--data", "[1,2,3]"]
    
    def test_dashes_in_value(self):
        """Test dashes in quoted value."""
        result = tokenize_line('--name "foo-bar-baz"')
        assert result == ["--name", "foo-bar-baz"]
    
    def test_underscores(self):
        """Test underscores in value."""
        result = tokenize_line("--var some_variable_name")
        assert result == ["--var", "some_variable_name"]
    
    def test_dots(self):
        """Test dots in value."""
        result = tokenize_line("--file config.production.fuc")
        assert result == ["--file", "config.production.fuc"]


class TestEdgeCases:
    """Test edge cases and unusual inputs."""
    
    def test_multiple_spaces_between_tokens(self):
        """Test multiple spaces between tokens."""
        result = tokenize_line("--name    myapp    --port   8080")
        assert result == ["--name", "myapp", "--port", "8080"]
    
    def test_tabs_as_separators(self):
        """Test tabs as token separators."""
        result = tokenize_line("--name\tmyapp\t--port\t8080")
        assert result == ["--name", "myapp", "--port", "8080"]
    
    def test_mixed_whitespace(self):
        """Test mixed whitespace (spaces and tabs)."""
        result = tokenize_line("--name  \t myapp \t  --port")
        assert result == ["--name", "myapp", "--port"]
    
    def test_quoted_empty_vs_unquoted_empty(self):
        """Test quoted empty strings are ignored but unquoted aren't an issue."""
        result = tokenize_line('--a "" --b value')
        assert result == ["--a", "--b", "value"]
    
    def test_unicode_characters(self):
        """Test unicode characters in values."""
        result = tokenize_line('--name "Café ☕"')
        assert result == ["--name", "Café ☕"]
    
    def test_newline_character_in_quotes(self):
        """Test that actual newlines in quotes work (though unusual)."""
        # This is a single logical line with \n character in string
        result = tokenize_line('--text "line\\nbreak"')
        assert result == ["--text", "line\\nbreak"]
    
    def test_numeric_values(self):
        """Test numeric values tokenize correctly."""
        result = tokenize_line("--port 8080 --timeout 30.5 --debug true")
        assert result == ["--port", "8080", "--timeout", "30.5", "--debug", "true"]
    
    def test_negative_numbers(self):
        """Test negative numbers."""
        result = tokenize_line("--offset -100 --ratio -0.5")
        assert result == ["--offset", "-100", "--ratio", "-0.5"]
    
    def test_value_starting_with_dash(self):
        """Test value starting with dash (requires quoting)."""
        result = tokenize_line('--note "--important"')
        assert result == ["--note", "--important"]
