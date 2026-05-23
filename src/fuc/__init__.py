"""FUC (Friendly User Config) - A simple, dataclass-based configuration library.

This library provides a unified interface for configuration management using:
- Dataclasses for schema definition
- .fuc files with command-line argument syntax
- Environment variables
- CLI arguments

All sources are merged with clear precedence rules.
"""

from .config import Fuc
from .InternalFuc import InternalFuc
from .errors import (
    FucError,
    ParseError,
    TypeCastError,
    DuplicateKeyError,
    UnknownKeyError,
)

__version__ = "0.1.0"
__all__ = [
    "Fuc",
    "InternalFuc",
    "FucError",
    "ParseError",
    "TypeCastError",
    "DuplicateKeyError",
    "UnknownKeyError",
]
