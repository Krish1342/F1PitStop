"""
Data loader module for Formula 1 session data.

This module provides functions to load F1 session data using the FastF1 library
with proper caching to avoid repeated downloads.
"""

import os
from pathlib import Path
from typing import Optional, Union

import fastf1
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


def load_session(
    year: int,
    gp: Union[str, int],
    session_type: str = "R",
    cache_dir: Optional[str] = None,
) -> fastf1.core.Session:
    """
    Load a Formula 1 session with caching enabled.

    This function loads a specific F1 session using the FastF1 library. It enables
    caching to avoid repeated downloads of the same data, significantly improving
    load times for previously accessed sessions.

    Args:
        year: The year of the Formula 1 season (e.g., 2024).
        gp: The Grand Prix identifier. Can be either:
            - An integer representing the round number (e.g., 5 for round 5)
            - A string with the GP name (e.g., "Monaco", "Silverstone")
        session_type: The type of session to load. Options:
            - "FP1": Free Practice 1
            - "FP2": Free Practice 2
            - "FP3": Free Practice 3
            - "Q": Qualifying
            - "S": Sprint
            - "SQ": Sprint Qualifying
            - "R": Race (default)
        cache_dir: Optional path to the cache directory. If None, uses the
            FASTF1_CACHE environment variable or "./cache" as default.

    Returns:
        A loaded FastF1 Session object containing all session data including
        laps, telemetry, and session information.

    Raises:
        ValueError: If the session cannot be found or loaded.
        Exception: If there's an error downloading or processing the data.

    Example:
        >>> session = load_session(2024, 5, "R")
        >>> print(f"Loaded: {session.event['EventName']} {session.name}")
        >>> laps = session.laps

    Notes:
        - First load of a session will download data (may take time).
        - Subsequent loads will use cached data (much faster).
        - Ensure you have enough disk space for the cache directory.
        - Set FASTF1_CACHE environment variable to customize cache location.
    """
    # Determine cache directory
    if cache_dir is None:
        cache_dir = os.getenv("FASTF1_CACHE", "./cache")

    # Create cache directory if it doesn't exist
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    # Enable caching
    fastf1.Cache.enable_cache(str(cache_path))

    try:
        # Get the session
        session = fastf1.get_session(year, gp, session_type)

        # Load all session data (laps, telemetry, etc.)
        print(f"Loading session: {year} {gp} {session_type}...")
        session.load()

        print(f"✓ Session loaded: {session.event['EventName']} - {session.name}")
        return session

    except Exception as e:
        error_msg = (
            f"Failed to load session {year}/{gp}/{session_type}. "
            f"Error: {str(e)}\n\n"
            "Suggestions:\n"
            "1. Check your internet connection.\n"
            "2. Verify the year, GP number/name, and session type are correct.\n"
            "3. Ensure the FASTF1_CACHE directory has write permissions.\n"
            f"4. Current cache directory: {cache_path}"
        )
        raise ValueError(error_msg) from e


def get_session_info(session: fastf1.core.Session) -> dict:
    """
    Extract key information from a loaded session.

    Args:
        session: A loaded FastF1 Session object.

    Returns:
        Dictionary containing session metadata including:
        - event_name: Name of the Grand Prix
        - session_name: Name of the session (e.g., "Race", "Qualifying")
        - circuit_name: Official circuit name
        - country: Country where the event takes place
        - location: City/location
        - date: Session date
        - total_laps: Number of laps in the session
        - drivers: List of driver codes who participated

    Example:
        >>> session = load_session(2024, 5, "R")
        >>> info = get_session_info(session)
        >>> print(f"{info['event_name']} at {info['circuit_name']}")
    """
    event_info = session.event

    # Get list of drivers who participated
    drivers = session.drivers if hasattr(session, "drivers") else []

    return {
        "event_name": event_info.get("EventName", "Unknown"),
        "session_name": session.name,
        "circuit_name": event_info.get("OfficialEventName", "Unknown Circuit"),
        "country": event_info.get("Country", "Unknown"),
        "location": event_info.get("Location", "Unknown"),
        "date": str(event_info.get("EventDate", "Unknown")),
        "total_laps": len(session.laps) if hasattr(session, "laps") else 0,
        "drivers": [str(d) for d in drivers],
    }
