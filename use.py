"""Demonstration of the FUC (Friendly User Config) library.

This example shows how to:
1. Define configuration schemas using dataclasses
2. Load configuration from multiple sources
3. Access configuration values
4. Write configuration files
5. Use CLI arguments and environment variables
"""

from dataclasses import dataclass, field
from pathlib import Path
from src.fuc import Fuc
import sys


# Step 1: Define your configuration schema using dataclasses
@dataclass
class DatabaseConfig:
    """Database connection settings"""
    host: str = "localhost"
    port: int = 5432
    name: str = "myapp"
    pool_size: int = 10
    timeout: float = 30.0
    use_ssl: bool = True


@dataclass
class ServerConfig:
    """HTTP server configuration"""
    host: str = "0.0.0.0"
    ports: list[int] = field(default_factory = lambda: [8080, 8443])
    workers: int = 4
    debug: bool = False


@dataclass
class AppConfig:
    """Main application configuration"""
    log_level: str = "INFO"
    database: DatabaseConfig = field(default_factory = DatabaseConfig)
    server: ServerConfig = field(default_factory = ServerConfig)


# Step 2: Initialize the configuration
def main():
    print("=" * 60)
    print("FUC (Friendly User Config) - Demonstration")
    print("=" * 60)

    # Load configuration with explicit parameters
    script_dir = Path(__file__).parent
    config = Fuc(AppConfig,
                 "use",
                 system_path = script_dir / "fuc_configs" / "system_config.fuc",
                 user_path = script_dir / "fuc_configs" / "user_config.fuc",
                 track_provenance = True,
                 cli_args = sys.argv[1:])

    print(f"\nConfiguration paths:")
    print(f"  System: {config.iFuc.system_path}")
    print(f"  User:   {config.iFuc.user_path}")
    print(f"  Env:    {config.iFuc.env_var}")

    # Step 3: Access configuration values
    print("\n" + "=" * 60)
    print("Configuration Values")
    print("=" * 60)

    print(f"\nApplication:")
    print(f"  Name:      {config.iFuc.app_name}")
    # print(f"  Version:   {config.version}")
    print(f"  Log Level: {config.log_level}")

    print(f"\nDatabase:")
    print(f"  Host:      {config.database.host}")
    print(f"  Port:      {config.database.port}")
    print(f"  Name:      {config.database.name}")
    print(f"  Pool Size: {config.database.pool_size}")
    print(f"  Timeout:   {config.database.timeout}s")
    print(f"  Use SSL:   {config.database.use_ssl}")

    print(f"\nServer:")
    print(f"  Host:      {config.server.host}")
    print(f"  Ports:     {config.server.ports}")
    print(f"  Workers:   {config.server.workers}")
    print(f"  Debug:     {config.server.debug}")

    # Step 4: Show provenance (where each value came from)
    if hasattr(config, '_provenance'):
        print("\n" + "=" * 60)
        print("Value Provenance (source of each configuration)")
        print("=" * 60)
        for key, source in sorted(config._provenance.items()):
            print(f"  {key:30s} <- {source}")

    # Step 5: Write configuration to file
    print("\n" + "=" * 60)
    print("Writing Configuration")
    print("=" * 60)

    try:
        config.write_user()
        print(f"✓ Configuration written to: {config.iFuc.user_path}")
        print("\nYou can now edit this file and the changes will be")
        print("loaded the next time you run this program!")
    except Exception as e:
        print(f"✗ Failed to write config: {e}")

    # Step 6: Usage examples
    print("\n" + "=" * 60)
    print("Usage Examples")
    print("=" * 60)

    env_prefix = f"FUC_{config.iFuc.app_name.upper()}"
    print(f"""
1. Run with defaults:
   python use.py

2. Override with CLI arguments:
   python use.py --log_level DEBUG --server.debug true --server.ports 3000 3001

3. Use a custom config file:
   python use.py --config /path/to/custom.fuc

4. Set via environment variables:
   export {config.iFuc.env_var}=/path/to/config.fuc
   export {env_prefix}_LOG_LEVEL=DEBUG
   export {env_prefix}_DATABASE_HOST=postgres.example.com
   export {env_prefix}_DATABASE_PORT=5433
   export {env_prefix}_SERVER_DEBUG=true
   python use.py

5. Edit the user config file:
   $EDITOR {config.iFuc.user_path}
   # Then run again to see changes
   python use.py
""")

    print("=" * 60)
    print("Configuration Priority (later wins):")
    print("=" * 60)
    print("""
1. Built-in defaults (dataclass defaults)
2. System config ({system_path})
3. User config ({user_path})
4. Env-selected config (${env_var})
5. CLI-selected config (--config path)
6. Environment variables ({env_prefix}_*)
7. CLI arguments (--key value)
""".format(
        system_path = config.iFuc.system_path,
        user_path = config.iFuc.user_path,
        env_var = config.iFuc.env_var,
        env_prefix = env_prefix,
    ))


if __name__ == "__main__":
    main()
