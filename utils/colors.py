"""
Color mapping utilities for drivers and tyre compounds.

This module provides consistent color schemes for visualizing F1 data,
including driver-specific colors and tyre compound colors.
"""

from typing import Tuple


def get_driver_color(driver_code: str) -> Tuple[int, int, int]:
    """
    Get a consistent RGB color for a driver based on their code.

    This function provides a deterministic color mapping for each driver,
    ensuring the same driver always appears with the same color across
    different sessions and visualizations.

    Args:
        driver_code: Three-letter driver code (e.g., "VER", "HAM", "LEC").

    Returns:
        Tuple of (R, G, B) values in range 0-255.

    Example:
        >>> color = get_driver_color("VER")
        >>> print(f"Verstappen's color: RGB{color}")

    Notes:
        - Colors are chosen to be visually distinct and accessible.
        - Uses a hash-based fallback for unknown drivers.
    """
    # Predefined colors for common drivers (based on team colors 2024)
    driver_colors = {
        # Red Bull Racing
        "VER": (30, 65, 255),  # Blue
        "PER": (255, 200, 0),  # Yellow-orange
        # Mercedes
        "HAM": (0, 210, 190),  # Teal
        "RUS": (165, 165, 165),  # Silver
        # Ferrari
        "LEC": (220, 0, 0),  # Red
        "SAI": (180, 0, 0),  # Dark red
        # McLaren
        "NOR": (255, 135, 0),  # Papaya orange
        "PIA": (255, 165, 50),  # Light papaya
        # Aston Martin
        "ALO": (0, 111, 98),  # Dark green
        "STR": (34, 153, 84),  # Green
        # Alpine
        "GAS": (255, 0, 130),  # Pink
        "OCO": (0, 144, 255),  # Blue
        # Williams
        "ALB": (0, 82, 255),  # Blue
        "SAR": (100, 196, 255),  # Light blue
        "COL": (100, 196, 255),  # Light blue
        # AlphaTauri / RB
        "TSU": (70, 155, 255),  # Light blue
        "RIC": (255, 200, 100),  # Yellow
        "LAW": (90, 175, 255),  # Sky blue
        # Alfa Romeo / Sauber
        "BOT": (155, 0, 60),  # Burgundy
        "ZHO": (200, 0, 70),  # Red-burgundy
        # Haas
        "MAG": (180, 180, 180),  # Light gray
        "HUL": (100, 100, 100),  # Dark gray
        "BEA": (200, 200, 200),  # Silver
        # Reserve/Other
        "DEV": (128, 128, 128),  # Gray
        "DRU": (255, 100, 100),  # Light red
        "LAT": (50, 150, 200),  # Blue
    }

    # Return predefined color if available
    if driver_code in driver_colors:
        return driver_colors[driver_code]

    # Hash-based color generation for unknown drivers
    # Ensures consistent color for same driver code
    hash_val = hash(driver_code)

    # Generate RGB values using hash
    r = (hash_val & 0xFF0000) >> 16
    g = (hash_val & 0x00FF00) >> 8
    b = hash_val & 0x0000FF

    # Ensure colors are bright enough to see
    r = max(r, 80)
    g = max(g, 80)
    b = max(b, 80)

    return (r, g, b)


def get_tyre_color(compound: str) -> Tuple[int, int, int]:
    """
    Get the standard F1 tyre compound color.

    Args:
        compound: Tyre compound name (e.g., "SOFT", "MEDIUM", "HARD",
            "INTERMEDIATE", "WET").

    Returns:
        Tuple of (R, G, B) values in range 0-255.

    Example:
        >>> color = get_tyre_color("SOFT")
        >>> print(f"Soft tyre color: RGB{color}")  # Red

    Notes:
        - Colors match official F1 tyre markings.
        - SOFT: Red
        - MEDIUM: Yellow
        - HARD: White
        - INTERMEDIATE: Green
        - WET: Blue
    """
    compound_colors = {
        "SOFT": (220, 0, 0),  # Red
        "MEDIUM": (255, 215, 0),  # Yellow/Gold
        "HARD": (240, 240, 240),  # White
        "INTERMEDIATE": (0, 180, 0),  # Green
        "WET": (0, 100, 255),  # Blue
        "UNKNOWN": (128, 128, 128),  # Gray
        "TEST_UNKNOWN": (255, 0, 255),  # Magenta (for testing)
    }

    # Normalize compound name
    compound_upper = compound.upper() if compound else "UNKNOWN"

    return compound_colors.get(compound_upper, compound_colors["UNKNOWN"])


def get_tyre_name(compound: str) -> str:
    """
    Get a user-friendly name for a tyre compound.

    Args:
        compound: Tyre compound code.

    Returns:
        Human-readable tyre name with explanation.

    Example:
        >>> print(get_tyre_name("SOFT"))
        Soft (fastest, least durable)
    """
    compound_names = {
        "SOFT": "Soft (fastest, least durable)",
        "MEDIUM": "Medium (balanced performance)",
        "HARD": "Hard (slowest, most durable)",
        "INTERMEDIATE": "Intermediate (light rain)",
        "WET": "Wet (heavy rain)",
        "UNKNOWN": "Unknown compound",
    }

    compound_upper = compound.upper() if compound else "UNKNOWN"
    return compound_names.get(compound_upper, compound_upper)


def rgb_to_normalized(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """
    Convert RGB values from 0-255 range to 0.0-1.0 range.

    Useful for libraries that expect normalized color values (e.g., matplotlib).

    Args:
        rgb: Tuple of (R, G, B) values in range 0-255.

    Returns:
        Tuple of (R, G, B) values in range 0.0-1.0.

    Example:
        >>> normalized = rgb_to_normalized((255, 128, 0))
        >>> print(normalized)  # (1.0, 0.5019..., 0.0)
    """
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def get_speed_heatmap_color(speed: float, max_speed: float) -> Tuple[int, int, int]:
    """
    Get a color representing speed as a heatmap (blue = slow, red = fast).

    Args:
        speed: Current speed value.
        max_speed: Maximum speed for normalization.

    Returns:
        Tuple of (R, G, B) values in range 0-255.

    Example:
        >>> color = get_speed_heatmap_color(150, 350)
        >>> # Returns a color between blue (slow) and red (fast)
    """
    if max_speed <= 0:
        return (128, 128, 128)  # Gray for invalid

    # Normalize speed to 0-1 range
    normalized = min(max(speed / max_speed, 0.0), 1.0)

    # Create gradient: Blue -> Cyan -> Green -> Yellow -> Red
    if normalized < 0.25:
        # Blue to Cyan
        t = normalized / 0.25
        r = 0
        g = int(255 * t)
        b = 255
    elif normalized < 0.5:
        # Cyan to Green
        t = (normalized - 0.25) / 0.25
        r = 0
        g = 255
        b = int(255 * (1 - t))
    elif normalized < 0.75:
        # Green to Yellow
        t = (normalized - 0.5) / 0.25
        r = int(255 * t)
        g = 255
        b = 0
    else:
        # Yellow to Red
        t = (normalized - 0.75) / 0.25
        r = 255
        g = int(255 * (1 - t))
        b = 0

    return (r, g, b)
