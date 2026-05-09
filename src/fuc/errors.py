"""Error classes for FUC with rich context information."""

from typing import Any, Optional, Union


class FucError(Exception):
    """Base exception for all FUC errors."""
    pass


class ParseError(FucError):
    """Raised when parsing fails."""
    
    def __init__(
        self,
        message: str,
        source: str = "",
        line: Optional[int] = None,
        key: str = "",
    ):
        self.message = message
        self.source = source
        self.line = line
        self.key = key
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [f"Error: {self.message}"]
        if self.source:
            parts.append(f"  Source: {self.source}")
        if self.line is not None:
            parts.append(f"  Line: {self.line}")
        if self.key:
            parts.append(f"  Key: {self.key}")
        return "\n".join(parts)


class TypeCastError(FucError):
    """Raised when type casting fails."""
    
    def __init__(
        self,
        key: str,
        expected: Union[type, object],
        received: Any,
        source: str = "",
        line: Optional[int] = None,
    ):
        self.key = key
        self.expected = expected
        self.received = received
        self.source = source
        self.line = line
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        # Handle both regular types and generic types
        if isinstance(self.expected, type):
            expected_name = self.expected.__name__
        else:
            expected_name = str(self.expected)
        parts = [f"Error: Invalid type for '{self.key}'"]
        if self.source:
            parts.append(f"  Source: {self.source}")
        if self.line is not None:
            parts.append(f"  Line: {self.line}")
        parts.append(f"  Key: {self.key}")
        parts.append(f"  Expected: {expected_name}")
        parts.append(f"  Received: {repr(self.received)}")
        return "\n".join(parts)


class DuplicateKeyError(FucError):
    """Raised when a key is defined multiple times in the same source."""
    
    def __init__(
        self,
        key: str,
        first_value: Any,
        duplicate_value: Any,
        source: str = "",
    ):
        self.key = key
        self.first_value = first_value
        self.duplicate_value = duplicate_value
        self.source = source
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [f"Error: Duplicate key '{self.key}'"]
        if self.source:
            parts.append(f"  Source: {self.source}")
        parts.append(f"  Key: {self.key}")
        parts.append(f"  First value: {repr(self.first_value)}")
        parts.append(f"  Duplicate value: {repr(self.duplicate_value)}")
        return "\n".join(parts)


class UnknownKeyError(FucError):
    """Raised when an unknown configuration key is encountered."""
    
    def __init__(
        self,
        key: str,
        valid_keys: list[str],
        source: str = "",
        line: Optional[int] = None,
    ):
        self.key = key
        self.valid_keys = valid_keys
        self.source = source
        self.line = line
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [f"Error: Unknown configuration key '{self.key}'"]
        if self.source:
            parts.append(f"  Source: {self.source}")
        if self.line is not None:
            parts.append(f"  Line: {self.line}")
        parts.append(f"  Key: {self.key}")
        if self.valid_keys:
            parts.append(f"  Valid keys: {', '.join(sorted(self.valid_keys))}")
        return "\n".join(parts)
