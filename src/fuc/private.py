"""InternalFuc dataclass for internal configuration."""

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InternalFuc:
    """Configuration for FUC's internal behavior.
    
    This dataclass allows customization of config file paths, environment
    variable names, and other internal settings. These settings cannot be
    overridden by users through config files or CLI arguments.
    
    Attributes:
        app_name: Name of the application (required)
        system_path: Path to system-wide config file
        user_path: Path to user-specific config file
        env_var: Environment variable name for config file path
        track_provenance: Whether to track the source of each config value
    """
    
    app_name: str
    system_path: str = ""
    user_path: str = ""
    env_var: str = ""
    track_provenance: bool = False
    
    def __post_init__(self):
        """Set OS-specific defaults if paths not provided."""
        # Set system_path default
        if not self.system_path:
            self.system_path = self._get_default_system_path()
        
        # Set user_path default
        if not self.user_path:
            self.user_path = self._get_default_user_path()
        
        # Set env_var default
        if not self.env_var:
            self.env_var = self._get_default_env_var()
    
    def _get_default_system_path(self) -> str:
        """Get OS-specific default system config path."""
        system = platform.system()
        
        if system == "Windows":
            # C:/ProgramData/{app_name}/config.fuc
            base = os.environ.get("PROGRAMDATA", "C:/ProgramData")
            return str(Path(base) / self.app_name / "config.fuc")
        else:
            # Linux/macOS: /etc/{app_name}/config.fuc
            return f"/etc/{self.app_name}/config.fuc"
    
    def _get_default_user_path(self) -> str:
        """Get OS-specific default user config path."""
        system = platform.system()
        
        if system == "Windows":
            # {APPDATA}/{app_name}/config.fuc
            base = os.environ.get("APPDATA", "")
            if not base:
                base = str(Path.home() / "AppData" / "Roaming")
            return str(Path(base) / self.app_name / "config.fuc")
        else:
            # Linux/macOS: ~/.config/{app_name}/config.fuc
            return str(Path.home() / ".config" / self.app_name / "config.fuc")
    
    def _get_default_env_var(self) -> str:
        """Get default environment variable name."""
        # FUC_{APP_NAME}_CONFIG (uppercase, spaces→underscores)
        sanitized = self.app_name.upper().replace(" ", "_").replace("-", "_")
        return f"FUC_{sanitized}_CONFIG"
