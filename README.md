# FUC - Friendly User Config

A Python configuration library that uses command-line argument syntax for config files.

## Overview

FUC (Friendly User Config) is a configuration management library that:

- Uses familiar command-line argument syntax in config files (`--key value`)
- Supports nested dataclass schemas with type safety
- Loads from multiple sources with clear precedence rules
- Provides attribute-based access (`config.database.host`)
- Tracks provenance (where each value came from)
- Supports CLI arguments and environment variables

## Installation



<!-- ```bash
pip install fuc
``` -->

```bash
pip install git+https://github.com/scottmonster/fuc.git

```
of

```
pip install git+https://github.com/scottmonster/fuc.git@branch-name
```

Or install editable:

```bash
git clone https://github.com/scottmonster/fuc.git
cd fuc
pip install -e .
```

## Quick Start

Define your configuration schema using dataclasses:

```python
from dataclasses import dataclass
from src.fuc import Fuc

@dataclass
class AppConfig:
    name: str = "MyApp"
    version: str = "1.0.0"
    debug: bool = False
    port: int = 8080

# Load configuration
config = Fuc(AppConfig, "myapp")

# Access values
print(config.name)    # "MyApp"
print(config.port)    # 8080
```

Create a config file at `~/.config/myapp/config.fuc`:

```
--name "Production App"
--port 3000
--debug false
```

## Features

### Command-Line Argument Syntax

Config files use familiar CLI syntax:

```
--name "My Application"
--port 8080
--debug
--database.host localhost
--database.port 5432
```

### Type Safety

Full support for Python type annotations:

- Primitives: `str`, `int`, `float`, `bool`
- Lists: `list[int]`, `list[str]`, `list[float]`
- Nested dataclasses with dot notation
- Automatic type casting and validation

### Multi-Source Loading

Configuration loads from multiple sources in priority order (later wins):

1. Built-in defaults (dataclass defaults)
2. System config (`/etc/{app_name}/config.fuc`)
3. User config (`~/.config/{app_name}/config.fuc`)
4. Environment-selected config (from `FUC_{APP_NAME}_CONFIG` variable)
5. CLI-selected config (`--config path/to/file.fuc`)
6. Environment variables (`FUC_{APP_NAME}_KEY=value`)
7. CLI arguments

### Provenance Tracking

Track where each configuration value originated:

```python
config = Fuc(AppConfig, "myapp", track_provenance=True)

print(config._provenance['name'])        # 'user_config'
print(config._provenance['debug'])       # 'cli'
print(config._provenance['port'])        # 'default'
```

### Nested Configuration

Use nested dataclasses for organized configuration:

```python
@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"

@dataclass
class AppConfig:
    app_name: str = "MyApp"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

config = Fuc(AppConfig, "myapp")
print(config.database.host)    # Access nested values
```

Config file:

```
--app_name "Production"
--database.host db.example.com
--database.port 5433
```

## File Format

### Basic Syntax

```
--key value
--nested.key value
--flag
```

### Comments

Full-line comments only (start with `#`):

```
# This is a comment
--name "My App"

# Another comment
--port 8080
```

Inline comments are not supported.

### String Values

```
--name Unquoted String       # "Unquoted String"
--name "Quoted String"       # "Quoted String"
--path /home/user/file.txt   # "/home/user/file.txt"
```

### Numeric Values

```
--port 8080                  # int: 8080
--rate 44.1                  # float: 44.1
```

### Boolean Values

```
--debug                      # True (standalone flag)
--debug true                 # True
--debug false                # False
```

Values are case-insensitive: `true`, `True`, `TRUE` all work.

### List Values

Lists of integers or floats (space or comma-separated):

```
--ports 8080 8081            # [8080, 8081]
--ports "8080, 8081"         # [8080, 8081]
--ports 8080,8081            # [8080, 8081]
```

Lists of strings (quoted, space-separated):

```
--servers "db.prod" "cache" "backup"       # ["db.prod", "cache", "backup"]
```

### None/Null Values

```
--timeout null               # None
--timeout none               # None
```

## API Reference

### Fuc Class

Initialize configuration:

```python
from src.fuc import Fuc
import sys

# Basic usage
config = Fuc(YourDataclassSchema, "myapp")

# With custom settings
config = Fuc(
    YourDataclassSchema,
    "myapp",
    track_provenance=True,
    system_path="/custom/path/config.fuc",
    user_path="/home/user/custom.fuc",
    env_var="MY_CUSTOM_CONFIG"
)

# With CLI arguments
config = Fuc(YourDataclassSchema, "myapp", cli_args=sys.argv[1:])
```

**Parameters:**
- `default_config` (type): Dataclass defining the configuration schema
- `app_name` (str): Name of the application (required)
- `cli_args` (Optional[list[str]]): CLI arguments to parse (default: None)
- `system_path` (str): Custom system config path (default: auto-generated)
- `user_path` (str): Custom user config path (default: auto-generated)
- `env_var` (str): Environment variable for config path (default: auto-generated)
- `track_provenance` (bool): Track source of each value (default: False)

### InternalFuc Class

Internal configuration settings (accessed via `config.iFuc`):

```python
# Access internal settings
print(config.iFuc.app_name)       # "myapp"
print(config.iFuc.system_path)    # "/etc/myapp/config.fuc"
print(config.iFuc.user_path)      # "~/.config/myapp/config.fuc"
print(config.iFuc.env_var)        # "FUC_MYAPP_CONFIG"
print(config.iFuc.track_provenance)  # True/False
```

Default paths by OS:

**Linux/macOS:**

- System: `/etc/{app_name}/config.fuc`
- User: `~/.config/{app_name}/config.fuc`

**Windows:**

- System: `C:/ProgramData/{app_name}/config.fuc`
- User: `{APPDATA}/{app_name}/config.fuc`

### Write Methods

Save configuration to files:

```python
# Write to user config path
config.write_user()

# Write to system config path (requires permissions)
config.write_system()

# Write to custom path
config.write("/path/to/custom.fuc")
```

Output format includes comments from dataclass docstrings.

### Environment Variables

Set configuration via environment variables:

```bash
# Top-level keys
export FUC_MYAPP_NAME="My App"
export FUC_MYAPP_PORT=3000

# Nested keys (use underscore instead of dot)
export FUC_MYAPP_DATABASE_HOST="db.example.com"
export FUC_MYAPP_DATABASE_PORT=5433
```

Format: `FUC_{APP_NAME}_{KEY}=value`

Keys are converted to lowercase with underscores replaced by dots.

### CLI Arguments

Override configuration via command line:

```bash
python app.py --name "CLI App" --port 3000 --debug true
python app.py --database.host db.example.com --database.port 5433
```

Use `--config path/to/file.fuc` to load a custom config file.

## Error Handling

FUC provides detailed error messages for configuration issues:

```
Error: Invalid type for 'port'
  Source: /home/user/.config/myapp/config.fuc
  Line: 5
  Key: port
  Expected: int
  Received: "abc"
```

Custom exception types:

- `FucError` - Base exception
- `ParseError` - Parsing errors
- `TypeCastError` - Type conversion errors
- `DuplicateKeyError` - Duplicate key definitions
- `UnknownKeyError` - Unknown configuration keys

## Example

See [use.py](use.py) for a complete demonstration including:

- Nested dataclass schemas
- Multi-source loading
- CLI argument overrides
- Environment variable usage
- Provenance tracking
- Writing configuration files

Run the example:

```bash
python use.py
python use.py --app_name "Custom" --server.debug true --server.ports 3000 3001
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
