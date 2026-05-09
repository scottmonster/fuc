"""Main Fuc class for loading and accessing configuration."""

from typing import Any, Optional
from .private import InternalFuc


class Fuc:
    """Configuration manager with multi-source loading.
    
    This class handles loading configuration from multiple sources with
    clear precedence rules:
    1. Built-in defaults (dataclass defaults)
    2. System config (system_path)
    3. User config (user_path)
    4. Env-selected config (path from env_var)
    5. CLI-selected config (--config path)
    6. Environment variables
    7. CLI arguments
    8. Validation
    
    Later sources override earlier ones.
    """
    
    def __init__(
        self,
        default_config: type,
        app_name: str,
        cli_args: Optional[list[str]] = None,
        system_path: str = "",
        user_path: str = "",
        env_var: str = "",
        track_provenance: bool = False,
    ):
        """Initialize the Config with a schema.
        
        Loads configuration from multiple sources with precedence:
        1. Built-in defaults
        2. System config
        3. User config
        4. Env-selected config
        5. CLI-selected config
        6. Environment variables
        7. CLI arguments
        
        Args:
            default_config: Dataclass type defining the configuration schema
            app_name: Application name (required, used for default paths)
            cli_args: Optional CLI arguments to parse (defaults to sys.argv[1:])
            system_path: Path to system config file (auto-generated if empty)
            user_path: Path to user config file (auto-generated if empty)
            env_var: Environment variable name for config path (auto-generated if empty)
            track_provenance: Track source of each configuration value
        
        Example:
            config = Config(AppConfig, "myapp")
            config = Config(AppConfig, "myapp", track_provenance=True)
        """
        from dataclasses import is_dataclass
        from .types import flatten_schema
        import sys
        import os
        
        if not is_dataclass(default_config):
            raise TypeError("default_config must be a dataclass")
        
        self._schema = default_config
        
        # Create InternalFuc from explicit parameters
        self.iFuc = InternalFuc(
            app_name=app_name,
            system_path=system_path,
            user_path=user_path,
            env_var=env_var,
            track_provenance=track_provenance,
        )
        
        # Flatten schema for easy type lookup
        self._flat_schema = flatten_schema(default_config)
        
        # Initialize values dict and provenance tracking
        self._values: dict[str, Any] = {}
        if self.iFuc.track_provenance:
            self._provenance: dict[str, str] = {}
        
        # Load defaults from dataclass
        self._load_defaults()
        
        # Load system config if exists
        if os.path.exists(self.iFuc.system_path):
            try:
                from .parser import parse_file
                system_config = parse_file(self.iFuc.system_path, self._schema)
                self._deep_merge(system_config, source='system_config')
            except Exception:
                pass  # Silently skip if system config has issues
        
        # Load user config if exists
        if os.path.exists(self.iFuc.user_path):
            try:
                from .parser import parse_file
                user_config = parse_file(self.iFuc.user_path, self._schema)
                self._deep_merge(user_config, source='user_config')
            except Exception:
                pass  # Silently skip if user config has issues
        
        # Load env-selected config if env var is set
        env_config_path = os.environ.get(self.iFuc.env_var)
        if env_config_path and os.path.exists(env_config_path):
            try:
                from .parser import parse_file
                env_config = parse_file(env_config_path, self._schema)
                self._deep_merge(env_config, source='env_config')
            except Exception:
                pass
        
        # Parse CLI arguments
        if cli_args is None:
            cli_args = sys.argv[1:]
        
        cli_config_path = None
        cli_values = {}
        if cli_args:
            from .parser import parse_cli
            cli_result = parse_cli(cli_args, self._schema)
            cli_config_path = cli_result['config_path']
            cli_values = cli_result['values']
        
        # Load CLI-selected config if --config was passed
        if cli_config_path and os.path.exists(cli_config_path):
            try:
                from .parser import parse_file
                cli_config = parse_file(cli_config_path, self._schema)
                self._deep_merge(cli_config, source='cli_config')
            except Exception:
                pass
        
        # Load environment variables
        env_vars = self._load_env_vars(self.iFuc.app_name)
        if env_vars:
            self._deep_merge(env_vars, source='env')
        
        # Load CLI arguments (highest priority)
        if cli_values:
            self._deep_merge(cli_values, source='cli')
    
    def _load_defaults(self) -> None:
        """Load default values from the dataclass schema."""
        from dataclasses import fields, is_dataclass, MISSING
        
        defaults = self._extract_defaults(self._schema)
        self._deep_merge(defaults, source='default')
    
    def _extract_defaults(self, schema: type, prefix: str = "") -> dict[str, Any]:
        """Extract default values from a dataclass schema.
        
        Args:
            schema: Dataclass to extract defaults from
            prefix: Prefix for nested keys
            
        Returns:
            Dictionary of default values (nested structure)
        """
        from dataclasses import fields, is_dataclass, MISSING
        
        result = {}
        
        for field in fields(schema):
            key = f"{prefix}.{field.name}" if prefix else field.name
            
            # Check if field has a default value
            has_default = field.default is not MISSING or field.default_factory is not MISSING
            
            if not has_default:
                continue
            
            # Get the default value
            if field.default is not MISSING:
                value = field.default
            elif field.default_factory is not MISSING:
                # default_factory - confirmed not MISSING so it's callable
                value = field.default_factory()
            else:
                continue
            
            # If the value is a dataclass instance, recursively extract its values
            if is_dataclass(value):
                nested = self._extract_defaults(type(value), prefix=key)
                # Merge nested structure into result
                for nested_key, nested_value in nested.items():
                    self._set_nested_value(result, nested_key, nested_value)
            else:
                self._set_nested_value(result, key, value)
        
        return result
    
    def _set_nested_value(self, d: dict, key: str, value: Any) -> None:
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
    
    def _deep_merge(self, source_dict: dict, source: str = "") -> None:
        """Deep merge a dictionary into _values.
        
        Args:
            source_dict: Dictionary to merge
            source: Source name for provenance tracking
        """
        self._deep_merge_recursive(self._values, source_dict, source, "")
    
    def _deep_merge_recursive(
        self,
        target: dict,
        source: dict,
        source_name: str,
        prefix: str
    ) -> None:
        """Recursively merge source into target.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
            source_name: Name of the source (for provenance)
            prefix: Current key prefix (for provenance)
        """
        for key, value in source.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively merge nested dicts
                self._deep_merge_recursive(target[key], value, source_name, full_key)
            else:
                # Replace value
                target[key] = value
                # Track provenance if enabled
                if self.iFuc.track_provenance:
                    self._provenance[full_key] = source_name
    
    def _load_env_vars(self, app_name: str) -> dict[str, Any]:
        """Load configuration from environment variables.
        
        Scans environment for variables matching FUC_{APP_NAME}_*
        and converts them to config keys.
        
        Args:
            app_name: Application name for variable prefix
            
        Returns:
            Dictionary of parsed configuration values (nested structure)
        """
        import os
        from .types import parse_value, get_field_type
        
        # Sanitize app name for env var prefix
        prefix = f"FUC_{app_name.upper().replace(' ', '_').replace('-', '_')}_"
        
        result = {}
        
        for env_name, env_value in os.environ.items():
            if not env_name.startswith(prefix):
                continue
            
            # Convert env var name to config key
            # FUC_MYAPP_APP_VERSION -> app.version
            key_part = env_name[len(prefix):]
            key = key_part.lower().replace('_', '.')
            
            # Get field type and parse
            try:
                field_type = get_field_type(self._schema, key)
                # Parse the value
                parsed = parse_value([env_value], field_type, key)
                self._set_nested_value(result, key, parsed)
            except Exception:
                # Skip invalid env vars
                continue
        
        return result
    
    def write(self, path: str) -> None:
        """Write current configuration to a file.
        
        Writes all configuration values with dataclass docstrings as comments.
        
        Args:
            path: Path to write the configuration file
        """
        import os
        from pathlib import Path
        from dataclasses import fields, is_dataclass
        from .parser import format_value
        from .types import get_field_type
        
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Flatten values into list of (key, value, docstring) tuples
        entries = []
        self._collect_write_entries(self._schema, self._values, "", entries)
        
        # Write to file
        with open(path, 'w', encoding='utf-8') as f:
            current_docstring = None
            
            for key, value, docstring in entries:
                # Write docstring as comment if it changed
                if docstring and docstring != current_docstring:
                    f.write(f"\n# {docstring}\n")
                    current_docstring = docstring
                elif not docstring and current_docstring:
                    f.write("\n")
                    current_docstring = None
                
                # Get field type for proper formatting
                field_type = get_field_type(self._schema, key)
                formatted_value = format_value(value, field_type)
                
                # Write the configuration line
                f.write(f"--{key} {formatted_value}\n")
    
    def _collect_write_entries(
        self,
        schema: type,
        values: dict,
        prefix: str,
        entries: list,
    ) -> None:
        """Recursively collect entries to write.
        
        Args:
            schema: Current dataclass schema
            values: Current values dict
            prefix: Current key prefix
            entries: List to append (key, value, docstring) tuples
        """
        from dataclasses import fields, is_dataclass
        
        # Get docstring from schema
        schema_docstring = schema.__doc__.strip() if schema.__doc__ else ""
        
        for field in fields(schema):
            key = f"{prefix}.{field.name}" if prefix else field.name
            
            if field.name not in values:
                continue
            
            value = values[field.name]
            
            # If nested dataclass, recurse
            if isinstance(value, dict):
                # Check if field.type is a dataclass type (not instance)
                field_type = field.type
                # Ensure field_type is a type (not an instance)
                if isinstance(field_type, type) and is_dataclass(field_type):
                    self._collect_write_entries(field_type, value, key, entries)
                else:
                    entries.append((key, value, schema_docstring))
            else:
                # Add entry with schema docstring
                entries.append((key, value, schema_docstring))
    
    def write_system(self) -> None:
        """Write configuration to system path."""
        self.write(self.iFuc.system_path)
    
    def write_user(self) -> None:
        """Write configuration to user path."""
        self.write(self.iFuc.user_path)
    
    def __getattr__(self, key: str) -> Any:
        """Get configuration value by attribute access.
        
        Supports nested access like config.app.version through proxy objects.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value or ConfigProxy for nested dicts
            
        Raises:
            AttributeError: If key doesn't exist
        """
        # Avoid recursion for internal attributes
        if key.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
        
        if key not in self._values:
            raise AttributeError(f"Configuration key '{key}' not found")
        
        value = self._values[key]
        
        # If value is a dict, return a proxy for nested access
        if isinstance(value, dict):
            return ConfigProxy(value)
        
        return value


class ConfigProxy:
    """Proxy object for nested configuration access."""
    
    def __init__(self, data: dict):
        self._data = data
    
    def __getattr__(self, key: str) -> Any:
        if key.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
        
        if key not in self._data:
            raise AttributeError(f"Configuration key '{key}' not found")
        
        value = self._data[key]
        
        # Recursively wrap nested dicts
        if isinstance(value, dict):
            return ConfigProxy(value)
        
        return value
    
    def __repr__(self) -> str:
        return f"ConfigProxy({self._data!r})"
