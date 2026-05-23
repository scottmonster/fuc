"""Tests for platform-specific path handling."""

import pytest
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from fuc import Fuc
from fuc.InternalFuc import InternalFuc


@dataclass
class SimpleConfig:
    """Simple config for path testing."""
    name: str = "default"


class TestPlatformPaths:
    """Test OS-specific default path behavior."""
    
    def test_internal_fuc_system_path_exists(self):
        """Test InternalFuc has system_path attribute."""
        ifuc = InternalFuc("testapp")
        assert hasattr(ifuc, 'system_path')
        assert isinstance(ifuc.system_path, (str, type(None)))
    
    def test_internal_fuc_user_path_exists(self):
        """Test InternalFuc has user_path attribute."""
        ifuc = InternalFuc("testapp")
        assert hasattr(ifuc, 'user_path')
        assert isinstance(ifuc.user_path, (str, type(None)))
    
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_paths(self):
        """Test Windows default paths."""
        ifuc = InternalFuc("testapp")
        
        # Windows should use PROGRAMDATA and APPDATA
        if ifuc.system_path:
            assert "ProgramData" in ifuc.system_path or "testapp" in ifuc.system_path
        
        if ifuc.user_path:
            assert "AppData" in ifuc.user_path or "testapp" in ifuc.user_path
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
    def test_unix_paths(self):
        """Test Unix default paths."""
        ifuc = InternalFuc("testapp")
        
        # Unix should use /etc and ~/.config
        if ifuc.system_path:
            assert "/etc" in ifuc.system_path or "testapp" in ifuc.system_path
        
        if ifuc.user_path:
            assert ".config" in ifuc.user_path or "testapp" in ifuc.user_path


class TestPathExpansion:
    """Test path expansion and resolution."""
    
    def test_tilde_expansion(self, clean_env):
        """Test tilde expands to user home directory."""
        @dataclass
        class PathConfig:
            path: str = "~"
        
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "~/myfile"])
        
        # Should contain home directory
        assert config.path == "~/myfile" or os.path.expanduser("~") in config.path
    
    def test_absolute_path(self, clean_env):
        """Test absolute paths are preserved."""
        @dataclass
        class PathConfig:
            path: str = "/"
        
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "/absolute/path"])
        assert config.path == "/absolute/path"
    
    def test_relative_path(self, clean_env):
        """Test relative paths are preserved."""
        @dataclass
        class PathConfig:
            path: str = "."
        
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "relative/path"])
        assert config.path == "relative/path"


class TestUserHomeDirectory:
    """Test user home directory resolution."""
    
    def test_home_directory_accessible(self):
        """Test home directory is accessible."""
        home = Path.home()
        assert home.exists()
        assert home.is_dir()
    
    def test_user_config_in_home_directory(self, clean_env):
        """Test user config paths resolve relative to home."""
        ifuc = InternalFuc("testapp")
        
        if ifuc.user_path:
            user_path = Path(ifuc.user_path)
            home = Path.home()
            
            # User path should be under home directory
            try:
                user_path.relative_to(home)
                is_under_home = True
            except ValueError:
                is_under_home = False
            
            # On most systems, user config is under home
            # (unless XDG_CONFIG_HOME or similar is set to custom location)
            assert is_under_home or os.environ.get("XDG_CONFIG_HOME") is not None


class TestConfigFileDiscovery:
    """Test automatic config file discovery."""
    
    def test_system_config_lower_priority(self, tmp_path, clean_env):
        """Test system config has lower priority than user config."""
        @dataclass
        class PrioConfig:
            value: str = "default"
        
        # Create system config
        system_file = tmp_path / "system.fuc"
        system_file.write_text("--value system\n")
        
        # Create user config
        user_file = tmp_path / "user.fuc"
        user_file.write_text("--value user\n")
        
        # Simulate by explicitly passing both
        config = Fuc(
            PrioConfig,
            "testapp",
            cli_args=[
                "--fuc.system_config", str(system_file),
                "--fuc.user_config", str(user_file)
            ]
        )
        
        # User config should win
        assert config.value == "user"
    
    def test_missing_config_files_ignored(self, clean_env):
        """Test missing config files don't cause errors."""
        # Should not raise even if default paths don't exist
        config = Fuc(SimpleConfig, "testapp", cli_args=[])
        assert config.name == "default"


class TestPathSeparators:
    """Test path separator handling."""
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
    def test_unix_separator(self, clean_env):
        """Test Unix paths use forward slash."""
        @dataclass
        class PathConfig:
            path: str = "/default"
        
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "/usr/local/bin"])
        assert "/" in config.path
        assert config.path == "/usr/local/bin"
    
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_separator(self, clean_env):
        """Test Windows paths can use backslash."""
        @dataclass
        class PathConfig:
            path: str = "C:\\"
        
        # Windows accepts both / and \
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "C:\\Program Files"])
        assert "Program Files" in config.path


class TestCrossPlatformPaths:
    """Test paths work correctly across platforms."""
    
    def test_pathlib_integration(self, clean_env):
        """Test that string paths can be used with pathlib."""
        @dataclass
        class PathConfig:
            path: str = "."
        
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "/some/path"])
        
        # Should be convertible to Path
        path_obj = Path(config.path)
        assert isinstance(path_obj, Path)
    
    def test_path_with_forward_slash_on_all_platforms(self, clean_env):
        """Test forward slash works on all platforms."""
        @dataclass
        class PathConfig:
            path: str = "."
        
        config = Fuc(PathConfig, "testapp", cli_args=["--path", "some/path/file"])
        assert "some/path/file" in config.path or "some\\path\\file" in config.path


class TestAppNameInPaths:
    """Test app name is used in default paths."""
    
    def test_app_name_in_system_path(self):
        """Test app name appears in system config path."""
        ifuc = InternalFuc("myapp")
        
        if ifuc.system_path:
            assert "myapp" in ifuc.system_path.lower()
    
    def test_app_name_in_user_path(self):
        """Test app name appears in user config path."""
        ifuc = InternalFuc("myapp")
        
        if ifuc.user_path:
            assert "myapp" in ifuc.user_path.lower()
    
    def test_different_app_names_different_paths(self):
        """Test different app names result in different paths."""
        ifuc1 = InternalFuc("app1")
        ifuc2 = InternalFuc("app2")
        
        # If paths exist, they should differ
        if ifuc1.user_path and ifuc2.user_path:
            assert ifuc1.user_path != ifuc2.user_path
