"""Example usage of the FUC configuration library."""

from dataclasses import dataclass, field
from src.fuc import Fuc


@dataclass
class AppConfig:
    """Application-specific configuration"""
    version: str = "4.2.0"
    ports: list[int] = field(default_factory=lambda: [8080, 8081])
    cert_file: str = "path/to/file.txt"
    host: str = "192.1.2.3"
    debug: bool = True


@dataclass
class DefaultConfig:
    """This is the default config"""
    name: str = "Bane Joe"
    username: str = "bj69"
    birth_year: int = 1969
    app: AppConfig = field(default_factory=AppConfig)


def main():
    """Demonstrate FUC configuration library usage."""
    
    # Initialize with new API
    config = Fuc(DefaultConfig, "myapp", track_provenance=True, cli_args=[])
    
    # Access configuration values
    print("Configuration Values:")
    print(f"  name: {config.name}")
    print(f"  username: {config.username}")
    print(f"  birth_year: {config.birth_year}")
    print(f"  app.version: {config.app.version}")
    print(f"  app.ports: {config.app.ports}")
    print(f"  app.cert_file: {config.app.cert_file}")
    print(f"  app.host: {config.app.host}")
    print(f"  app.debug: {config.app.debug}")
    
    # Show provenance if enabled
    if hasattr(config, '_provenance'):
        print("\nProvenance:")
        for key, source in config._provenance.items():
            print(f"  {key}: {source}")
    
    # Write user config
    print(f"\nWriting user config to: {config.iFuc.user_path}")
    try:
        config.write_user()
        print("  ✓ Config written successfully")
    except Exception as e:
        print(f"  ✗ Failed to write config: {e}")
    
    print("\n✓ FUC library is working!")


if __name__ == "__main__":
    main()
