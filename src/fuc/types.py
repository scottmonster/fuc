"""Type casting and schema introspection utilities."""

from typing import Any, Union, get_args, get_origin


def parse_value(values: list[str], field_type: Union[type, object], key: str) -> Any:
    """Parse string values to the appropriate type.
    
    Type-aware parsing with the following rules:
    - bool: Case-insensitive true/false, standalone flag = True
    - None: Case-insensitive null/none
    - list[str]: Each value is a separate element (must be quoted)
    - list[int], list[float]: Split on comma/whitespace and cast
    - int, float, str: Cast single value
    
    Args:
        values: List of string values to parse
        field_type: Target type to cast to (may be generic like list[int])
        key: Configuration key (for error reporting)
        
    Returns:
        Parsed value of the appropriate type
        
    Raises:
        TypeCastError: If type casting fails
    """
    from .errors import TypeCastError, ParseError
    
    # Handle None/null
    if len(values) == 1 and values[0].lower() in ('null', 'none'):
        return None
    
    # Get origin type (for generics like list[int])
    origin = get_origin(field_type)
    
    # Handle list types
    if origin is list:
        element_type = get_args(field_type)[0]
        
        if element_type == str:
            # list[str]: Each value is already a separate element
            return values
        else:
            # list[int], list[float]: Split on comma/whitespace and cast
            all_elements = []
            for val in values:
                # Split on comma and/or whitespace
                parts = val.replace(',', ' ').split()
                for part in parts:
                    part = part.strip()
                    if part:
                        try:
                            all_elements.append(_cast_primitive(part, element_type))
                        except (ValueError, TypeError) as e:
                            raise TypeCastError(
                                key=key,
                                expected=element_type,
                                received=part,
                            )
            return all_elements
    
    # Handle boolean
    if field_type == bool:
        if len(values) != 1:
            raise ParseError(f"Boolean {key} expects single value, got {len(values)}", key=key)
        val = values[0].lower()
        if val in ('true', '1', 'yes'):
            return True
        elif val in ('false', '0', 'no'):
            return False
        else:
            raise TypeCastError(
                key=key,
                expected=bool,
                received=values[0],
            )
    
    # Single value
    if len(values) != 1:
        raise ParseError(
            f"{key} expects single value, got {len(values)}",
            key=key,
        )
    
    try:
        return _cast_primitive(values[0], field_type)
    except (ValueError, TypeError) as e:
        raise TypeCastError(
            key=key,
            expected=field_type,
            received=values[0],
        )


def _cast_primitive(value: str, target_type: Union[type, object]) -> Any:
    """Cast a string value to a primitive type.
    
    Args:
        value: String value to cast
        target_type: Target type (int, float, str, or generic type)
        
    Returns:
        Casted value
        
    Raises:
        ValueError: If casting fails
    """
    if target_type == int or target_type is int:
        return int(value)
    elif target_type == float or target_type is float:
        return float(value)
    elif target_type == str or target_type is str:
        return value
    else:
        raise ValueError(f"Unsupported type: {target_type}")


def get_field_type(schema: type, key: str) -> Union[type, object]:
    """Get the type of a field from a dataclass schema.
    
    Supports dot notation for nested fields (e.g., "app.version").
    
    Args:
        schema: Dataclass type
        key: Field name (supports dot notation for nested fields)
        
    Returns:
        Type of the field (may be generic type like list[int])
        
    Raises:
        AttributeError: If field doesn't exist
    """
    from dataclasses import fields, is_dataclass
    
    parts = key.split('.')
    current_type: Union[type, object] = schema
    
    for part in parts:
        if not is_dataclass(current_type):
            raise AttributeError(f"'{current_type}' is not a dataclass, cannot access field '{part}'")
        
        # Find the field
        field_found = False
        for field in fields(current_type):
            if field.name == part:
                current_type = field.type
                field_found = True
                break
        
        if not field_found:
            raise AttributeError(f"Field '{part}' not found in {current_type}")
    
    return current_type


def flatten_schema(schema: type, prefix: str = "") -> dict[str, Union[type, object]]:
    """Flatten a dataclass schema into a dictionary of all keys and their types.
    
    Recursively flattens nested dataclasses using dot notation.
    
    Args:
        schema: Dataclass type to flatten
        prefix: Prefix for nested keys (used internally)
        
    Returns:
        Dictionary mapping key paths to types (including generic types)
    """
    from dataclasses import fields, is_dataclass
    
    result: dict[str, Union[type, object]] = {}
    
    if not is_dataclass(schema):
        return result
    
    for field in fields(schema):
        # Prevent 'fuc' as a config key name
        if field.name == "fuc":
            raise ValueError(
                "Config schema cannot have a field named 'fuc' - "
                "this name is reserved for FUC internal settings. "
                "Please use a different field name."
            )
        
        key = f"{prefix}.{field.name}" if prefix else field.name
        
        # Check if this is a nested dataclass
        field_type = field.type
        origin = get_origin(field_type)
        
        # If it's not a generic type and is a dataclass type (not instance), recurse
        if origin is None and isinstance(field_type, type) and is_dataclass(field_type):
            # Recursively flatten nested dataclasses
            result.update(flatten_schema(field_type, prefix=key))
        else:
            # Regular field or generic type (like list[int])
            result[key] = field_type
    
    return result


def validate_key(key: str, schema: type) -> bool:
    """Check if a key exists in the schema.
    
    Supports dot notation for nested fields.
    
    Args:
        key: Key to validate (supports dot notation)
        schema: Dataclass schema
        
    Returns:
        True if key exists, False otherwise
    """
    try:
        get_field_type(schema, key)
        return True
    except (AttributeError, IndexError):
        return False
