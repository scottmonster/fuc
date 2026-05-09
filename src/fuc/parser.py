"""Parser for FUC configuration files and CLI arguments."""

from typing import Any, Union


def tokenize_line(line: str) -> list[str]:
    """Tokenize a line with quote-aware splitting.
    
    Handles both single and double quotes. Whitespace inside quotes is preserved.
    Splits on whitespace outside quotes.
    
    Args:
        line: The line to tokenize
        
    Returns:
        List of tokens extracted from the line
        
    Examples:
        >>> tokenize_line('--name "Bane Joe"')
        ['--name', 'Bane Joe']
        >>> tokenize_line('--servers "a" "b" "c"')
        ['--servers', 'a', 'b', 'c']
        >>> tokenize_line('--path /some/path')
        ['--path', '/some/path']
    """
    tokens = []
    current = ""
    in_quote = False
    quote_char = None
    
    for char in line:
        if char in ('"', "'") and not in_quote:
            # Start of quoted string
            in_quote = True
            quote_char = char
        elif char == quote_char and in_quote:
            # End of quoted string
            in_quote = False
            quote_char = None
            if current:
                tokens.append(current)
                current = ""
        elif char.isspace() and not in_quote:
            # Whitespace outside quotes - token separator
            if current:
                tokens.append(current)
                current = ""
        else:
            # Regular character or whitespace inside quotes
            current += char
    
    # Don't forget the last token
    if current:
        tokens.append(current)
    
    return tokens


def parse_tokens(tokens: list[str], schema: type, source: str = "CLI") -> dict[str, Any]:
    """Parse tokens into a dictionary of key-value pairs.
    
    Tokens should be in the format: --key value1 value2 --key2 value3
    
    Args:
        tokens: List of tokens to parse
        schema: Dataclass type defining the configuration schema
        source: Source name for error reporting
        
    Returns:
        Dictionary of parsed configuration values (nested structure for dot notation)
        
    Raises:
        ParseError: If token format is invalid
        DuplicateKeyError: If the same key appears multiple times
    """
    from .types import get_field_type, validate_key
    from .errors import ParseError, DuplicateKeyError
    
    result = {}
    i = 0
    seen_keys = set()
    
    while i < len(tokens):
        token = tokens[i]
        
        # Must start with --
        if not token.startswith('--'):
            raise ParseError(
                f"Expected flag starting with --, got: {token}",
                source=source,
            )
        
        key = token[2:]  # Remove --
        
        # Check for duplicate keys
        if key in seen_keys:
            raise DuplicateKeyError(
                key=key,
                first_value=result.get(key),
                duplicate_value="<pending>",
                source=source,
            )
        seen_keys.add(key)
        
        # Validate key exists in schema
        if not validate_key(key, schema):
            from .types import flatten_schema
            valid_keys = list(flatten_schema(schema).keys())
            from .errors import UnknownKeyError
            raise UnknownKeyError(
                key=key,
                valid_keys=valid_keys,
                source=source,
            )
        
        field_type = get_field_type(schema, key)
        
        # Check if this is a boolean flag (standalone)
        if field_type == bool:
            # Peek at next token
            if i + 1 >= len(tokens) or tokens[i + 1].startswith('--'):
                # Standalone flag means True
                _set_nested_value(result, key, True)
                i += 1
                continue
        
        # Collect values until next key or end
        values = []
        i += 1
        while i < len(tokens) and not tokens[i].startswith('--'):
            values.append(tokens[i])
            i += 1
        
        # No values provided
        if not values:
            if field_type == bool:
                _set_nested_value(result, key, True)
            else:
                raise ParseError(
                    f"No value provided for {key}",
                    source=source,
                    key=key,
                )
            continue
        
        # Parse based on type
        from .types import parse_value
        parsed_value = parse_value(values, field_type, key)
        _set_nested_value(result, key, parsed_value)
    
    return result


def _set_nested_value(d: dict, key: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation.
    
    Args:
        d: Dictionary to modify
        key: Key (may contain dots for nesting)
        value: Value to set
    """
    parts = key.split('.')
    current = d
    
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    current[parts[-1]] = value


def parse_file(path: str, schema: type) -> dict[str, Any]:
    """Parse a .fuc configuration file.
    
    Reads the file line-by-line, skips comments and empty lines,
    tokenizes valid lines, and parses them into a configuration dict.
    
    Args:
        path: Path to the .fuc file
        schema: Dataclass type defining the configuration schema
        
    Returns:
        Dictionary of parsed configuration values (nested structure)
        
    Raises:
        ParseError: If file parsing fails
        FileNotFoundError: If file doesn't exist
    """
    import os
    from .errors import ParseError, TypeCastError, UnknownKeyError
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    all_tokens = []
    line_map = {}  # Map token index to line number for error reporting
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Tokenize the line
            tokens = tokenize_line(line)
            
            # Track which line each token came from
            for token in tokens:
                line_map[len(all_tokens)] = line_num
                all_tokens.append(token)
    
    # Parse all collected tokens
    try:
        return parse_tokens(all_tokens, schema, source=path)
    except (ParseError, TypeCastError, UnknownKeyError) as e:
        # Try to add line number context if we can
        if not e.line and all_tokens and line_map:
            # Find the first token index to estimate line number
            e.line = line_map.get(0, 1)
        raise
    except Exception:
        # Re-raise other exceptions as-is
        raise


def parse_cli(args: list[str], schema: type) -> dict[str, Any]:
    """Parse CLI arguments.
    
    Handles special --config flag separately and returns both
    the config path (if present) and the parsed arguments.
    
    Args:
        args: List of command-line arguments (sys.argv style)
        schema: Dataclass type defining the configuration schema
        
    Returns:
        Dictionary with two keys:
        - 'config_path': Path from --config flag (or None)
        - 'values': Parsed configuration values (nested structure)
        
    Raises:
        ParseError: If parsing fails
    """
    # Filter out --config and its value
    config_path = None
    filtered_args = []
    
    i = 0
    while i < len(args):
        if args[i] == '--config':
            # Get the config path
            if i + 1 < len(args):
                config_path = args[i + 1]
                i += 2
            else:
                from .errors import ParseError
                raise ParseError("--config requires a path argument", source="CLI")
        else:
            filtered_args.append(args[i])
            i += 1
    
    # Parse remaining arguments
    values = parse_tokens(filtered_args, schema, source="CLI") if filtered_args else {}
    
    return {
        'config_path': config_path,
        'values': values,
    }


def format_value(value: Any, field_type: Union[type, object]) -> str:
    """Format a Python value back to .fuc syntax.
    
    Handles quoting for strings, list formatting, and boolean formatting.
    
    Args:
        value: The value to format
        field_type: The type of the field (may be generic like list[int])
        
    Returns:
        Formatted string representation suitable for .fuc files
    """
    from typing import get_origin, get_args
    
    if value is None:
        return "null"
    
    origin = get_origin(field_type)
    
    # Handle lists
    if origin is list:
        element_type = get_args(field_type)[0]
        
        if element_type == str:
            # list[str]: Space-separated quoted strings
            return ' '.join(f'"{item}"' for item in value)
        else:
            # list[int], list[float]: Space-separated values
            return ' '.join(str(item) for item in value)
    
    # Handle bool
    if isinstance(value, bool):
        return 'true' if value else 'false'
    
    # Handle numbers
    if isinstance(value, (int, float)):
        return str(value)
    
    # Handle strings
    if isinstance(value, str):
        # Quote if string contains special characters or spaces
        needs_quote = any(char in value for char in [
            ' ', '\t', '#', '$', '&', '|', ';', '<', '>', '(', ')',
            '[', ']', '{', '}', '*', '?', '~', '`', '"', "'", '\\'
        ])
        
        if needs_quote:
            # Escape any existing quotes
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value
    
    # Fallback
    return str(value)
