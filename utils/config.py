"""
Configuration management utilities.

This module provides centralized configuration loading and validation.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """
    Application configuration loaded from environment variables.

    This class provides type-safe access to configuration values with
    sensible defaults.
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            env_file: Optional path to .env file. If None, loads from default location.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

    @property
    def cache_dir(self) -> Path:
        """Get the FastF1 cache directory path."""
        cache_path = os.getenv("FASTF1_CACHE", "./cache")
        path = Path(cache_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def telemetry_frequency(self) -> int:
        """Get the telemetry resampling frequency in Hz."""
        return int(os.getenv("TELEMETRY_FREQUENCY_HZ", "10"))

    @property
    def turn_detection_threshold(self) -> float:
        """Get the turn detection threshold in degrees."""
        return float(os.getenv("TURN_DETECTION_THRESHOLD", "15"))

    @property
    def default_speed_multiplier(self) -> float:
        """Get the default replay speed multiplier."""
        return float(os.getenv("DEFAULT_SPEED_MULTIPLIER", "1.0"))

    @property
    def fastf1_username(self) -> Optional[str]:
        """Get FastF1 username if configured."""
        username = os.getenv("FASTF1_USERNAME", "")
        return username if username else None

    @property
    def fastf1_password(self) -> Optional[str]:
        """Get FastF1 password if configured."""
        password = os.getenv("FASTF1_PASSWORD", "")
        return password if password else None


# Global config instance
config = Config()
