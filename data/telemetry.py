"""
Telemetry processing module for Formula 1 data analysis.

This module provides functions to extract, process, and analyze telemetry data
from F1 sessions, including driver telemetry extraction, time-based interpolation,
turn detection, and speed analysis.
"""

import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import fastf1
from scipy.interpolate import interp1d
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


def extract_driver_telemetry(
    session: fastf1.core.Session, driver_code: str
) -> pd.DataFrame:
    """
    Extract complete telemetry data for a specific driver from a session.

    This function retrieves all telemetry data for a given driver, including
    position (X, Y coordinates), speed, gear, throttle, brake, and tyre compound
    information across all laps in the session.

    Args:
        session: A loaded FastF1 Session object.
        driver_code: Three-letter driver code (e.g., "VER", "HAM", "LEC").

    Returns:
        DataFrame with columns:
        - Time: Timestamp (datetime64)
        - SessionTime: Seconds from session start (float)
        - X: Track X-coordinate in meters (float)
        - Y: Track Y-coordinate in meters (float)
        - Speed: Speed in km/h (float)
        - nGear: Current gear (int)
        - Throttle: Throttle percentage 0-100 (float)
        - Brake: Brake pressure 0-100 (float)
        - Compound: Tyre compound name (str: SOFT, MEDIUM, HARD, etc.)
        - LapNumber: Current lap number (int)
        - Distance: Distance along track in meters (float)

    Raises:
        ValueError: If driver code is not found in the session.

    Example:
        >>> session = load_session(2024, 5, "R")
        >>> telemetry = extract_driver_telemetry(session, "VER")
        >>> print(f"Max speed: {telemetry['Speed'].max():.1f} km/h")

    Notes:
        - Telemetry is sampled at varying rates (typically 3-10 Hz).
        - Some fields may contain NaN values if data is unavailable.
        - Use build_common_timebase() to resample multiple drivers to same rate.
    """
    # Get driver laps
    try:
        driver_laps = session.laps.pick_driver(driver_code)
    except Exception as e:
        raise ValueError(
            f"Driver '{driver_code}' not found in session. "
            f"Available drivers: {session.drivers}"
        ) from e

    if driver_laps.empty:
        raise ValueError(f"No laps found for driver '{driver_code}'")

    # Collect telemetry from all laps
    telemetry_list = []

    for idx, lap in driver_laps.iterrows():
        try:
            # Get telemetry for this lap
            lap_telemetry = lap.get_telemetry()

            if lap_telemetry.empty:
                continue

            # Add lap number and compound information
            lap_telemetry["LapNumber"] = lap["LapNumber"]
            lap_telemetry["Compound"] = (
                lap["Compound"] if pd.notna(lap["Compound"]) else "UNKNOWN"
            )

            telemetry_list.append(lap_telemetry)

        except Exception as e:
            print(f"Warning: Could not load telemetry for lap {lap['LapNumber']}: {e}")
            continue

    if not telemetry_list:
        raise ValueError(f"No telemetry data available for driver '{driver_code}'")

    # Combine all laps
    full_telemetry = pd.concat(telemetry_list, ignore_index=True)

    # Ensure SessionTime column exists (seconds from session start)
    if "SessionTime" not in full_telemetry.columns and "Time" in full_telemetry.columns:
        # Convert Time to SessionTime (seconds from start)
        full_telemetry["SessionTime"] = full_telemetry["Time"].dt.total_seconds()

    # Select and order relevant columns
    columns_to_keep = [
        "Time",
        "SessionTime",
        "X",
        "Y",
        "Speed",
        "nGear",
        "Throttle",
        "Brake",
        "Compound",
        "LapNumber",
        "Distance",
    ]

    # Keep only columns that exist
    available_columns = [
        col for col in columns_to_keep if col in full_telemetry.columns
    ]
    result = full_telemetry[available_columns].copy()

    # Sort by time
    if "SessionTime" in result.columns:
        result = result.sort_values("SessionTime").reset_index(drop=True)

    return result


def build_common_timebase(
    telemetry_dict: Dict[str, pd.DataFrame], hz: int = 10
) -> np.ndarray:
    """
    Create a common time base for multiple drivers and resample their telemetry.

    This function creates a uniform time grid and interpolates all drivers' telemetry
    data to this common timebase, enabling synchronized replay and comparison.

    Algorithm:
    1. Find the earliest and latest timestamps across all drivers.
    2. Create a uniform time grid at the specified frequency (Hz).
    3. For each driver, interpolate their telemetry onto this time grid.
    4. Handle missing data by forward-filling or marking as NaN.

    Args:
        telemetry_dict: Dictionary mapping driver codes to their telemetry DataFrames.
            Each DataFrame should have a 'SessionTime' column in seconds.
        hz: Target frequency in Hz (samples per second). Default is 10 Hz.
            Adjustable based on performance needs:
            - 5 Hz: Lower resource usage, acceptable for visualization
            - 10 Hz: Good balance (default)
            - 20 Hz: Higher fidelity, more resource intensive

    Returns:
        Numpy array of timestamps in seconds representing the common timebase.
        The telemetry_dict DataFrames are modified in-place to include interpolated data.

    Example:
        >>> telemetry = {
        ...     "VER": extract_driver_telemetry(session, "VER"),
        ...     "HAM": extract_driver_telemetry(session, "HAM")
        ... }
        >>> timeline = build_common_timebase(telemetry, hz=10)
        >>> print(f"Timeline: {len(timeline)} samples at 10 Hz")

    Notes:
        - TODO: Adjust hz parameter based on visualization performance.
        - Linear interpolation is used for continuous values (Speed, X, Y).
        - Nearest-neighbor is used for discrete values (Gear, Compound).
        - Gaps larger than 5 seconds are marked as missing data.
    """
    if not telemetry_dict:
        return np.array([])

    # Find global time range across all drivers
    min_time = float("inf")
    max_time = float("-inf")

    for driver_code, telemetry in telemetry_dict.items():
        if telemetry.empty or "SessionTime" not in telemetry.columns:
            print(f"Warning: No SessionTime data for {driver_code}, skipping")
            continue

        # Convert SessionTime to seconds (float) if it's a Timedelta
        session_time = telemetry["SessionTime"]
        if hasattr(session_time.iloc[0], "total_seconds"):
            # It's a Timedelta, convert to seconds
            telemetry["SessionTime"] = session_time.dt.total_seconds()

        driver_min = telemetry["SessionTime"].min()
        driver_max = telemetry["SessionTime"].max()

        min_time = min(min_time, driver_min)
        max_time = max(max_time, driver_max)

    if min_time == float("inf"):
        raise ValueError("No valid SessionTime data found in any telemetry")

    # Create common time base
    dt = 1.0 / hz  # Time step in seconds
    common_timebase = np.arange(min_time, max_time, dt)

    print(
        f"Common timebase: {len(common_timebase)} samples from {min_time:.1f}s to {max_time:.1f}s at {hz} Hz"
    )

    # Interpolate each driver's telemetry to the common timebase
    for driver_code, telemetry in telemetry_dict.items():
        if telemetry.empty or "SessionTime" not in telemetry.columns:
            continue

        # Original timestamps
        original_times = telemetry["SessionTime"].values

        # Create interpolated data dictionary
        interpolated_data = {"SessionTime": common_timebase}

        # Columns to interpolate with different methods
        continuous_cols = ["X", "Y", "Speed", "Throttle", "Brake", "Distance"]
        discrete_cols = ["nGear", "LapNumber"]

        for col in continuous_cols:
            if col in telemetry.columns:
                # Remove NaN values for interpolation
                valid_mask = telemetry[col].notna()
                if valid_mask.sum() > 1:
                    try:
                        # Linear interpolation
                        f = interp1d(
                            original_times[valid_mask],
                            telemetry[col].values[valid_mask],
                            kind="linear",
                            bounds_error=False,
                            fill_value=np.nan,
                        )
                        interpolated_data[col] = f(common_timebase)
                    except Exception as e:
                        print(
                            f"Warning: Could not interpolate {col} for {driver_code}: {e}"
                        )
                        interpolated_data[col] = np.full(len(common_timebase), np.nan)
                else:
                    interpolated_data[col] = np.full(len(common_timebase), np.nan)

        for col in discrete_cols:
            if col in telemetry.columns:
                valid_mask = telemetry[col].notna()
                if valid_mask.sum() > 0:
                    try:
                        # Nearest neighbor interpolation for discrete values
                        f = interp1d(
                            original_times[valid_mask],
                            telemetry[col].values[valid_mask],
                            kind="nearest",
                            bounds_error=False,
                            fill_value=np.nan,
                        )
                        interpolated_data[col] = f(common_timebase)
                    except Exception as e:
                        print(
                            f"Warning: Could not interpolate {col} for {driver_code}: {e}"
                        )
                        interpolated_data[col] = np.full(len(common_timebase), np.nan)
                else:
                    interpolated_data[col] = np.full(len(common_timebase), np.nan)

        # Handle compound (tyre type) - use forward fill
        if "Compound" in telemetry.columns:
            compounds = []
            current_compound = "UNKNOWN"

            for t in common_timebase:
                # Find the most recent compound at this time
                mask = original_times <= t
                if mask.any():
                    recent_compounds = telemetry.loc[mask, "Compound"]
                    if not recent_compounds.empty:
                        last_compound = recent_compounds.iloc[-1]
                        if pd.notna(last_compound):
                            current_compound = last_compound
                compounds.append(current_compound)

            interpolated_data["Compound"] = compounds

        # Update the telemetry dictionary with interpolated data
        telemetry_dict[driver_code] = pd.DataFrame(interpolated_data)

    return common_timebase


def _infer_turns_from_track(track_coords: np.ndarray) -> List[Dict]:
    """Legacy geometric turn detection kept as a fallback for tests/offline use."""
    threshold_deg = float(os.getenv("TURN_DETECTION_THRESHOLD", "15"))

    if track_coords is None or len(track_coords) < 3:
        return []

    tangents = np.diff(track_coords, axis=0)
    headings_deg = np.degrees(np.arctan2(tangents[:, 1], tangents[:, 0]))
    heading_changes = np.diff(headings_deg)
    heading_changes = np.where(heading_changes > 180, heading_changes - 360, heading_changes)
    heading_changes = np.where(heading_changes < -180, heading_changes + 360, heading_changes)

    abs_changes = np.abs(heading_changes)
    corner_indices = np.where(abs_changes > threshold_deg)[0] + 1

    if len(corner_indices) == 0:
        print(f"No turns detected with threshold {threshold_deg}°")
        return []

    merge_distance = 50.0  # meters
    turns = []
    i = 0

    while i < len(corner_indices):
        start_idx = corner_indices[i]
        current_group = [start_idx]

        j = i + 1
        while j < len(corner_indices):
            next_idx = corner_indices[j]
            dist = np.linalg.norm(track_coords[next_idx] - track_coords[start_idx])
            if dist < merge_distance:
                current_group.append(next_idx)
                j += 1
            else:
                break

        apex_idx = current_group[len(current_group) // 2]

        if apex_idx < len(heading_changes):
            total_heading_change = sum(
                heading_changes[idx]
                for idx in current_group
                if idx < len(heading_changes)
            )

            segment_lengths = np.linalg.norm(tangents, axis=1)
            arc_length = sum(
                segment_lengths[idx]
                for idx in current_group
                if idx < len(segment_lengths)
            )

            heading_change_rad = np.radians(abs(total_heading_change))
            radius = arc_length / heading_change_rad if heading_change_rad > 0 else 0

            turns.append(
                {
                    "index": int(apex_idx),
                    "x": float(track_coords[apex_idx, 0]),
                    "y": float(track_coords[apex_idx, 1]),
                    "radius": float(radius),
                    "heading_change": float(total_heading_change),
                    "name": f"Turn {len(turns) + 1}",
                }
            )

        i = j if j > i else i + 1

    print(f"Detected {len(turns)} turns with threshold {threshold_deg}° (fallback)")
    return turns


def compute_turns(
    track_coords: Optional[np.ndarray] = None,
    session: Optional[fastf1.core.Session] = None,
) -> List[Dict]:
    """
    Get official corner data from FastF1 circuit info when available; otherwise fall back to geometric detection.

    Args:
        track_coords: Optional track centerline coordinates for fallback detection.
        session: Loaded FastF1 session to query official corner metadata.

    Returns:
        List of turn dictionaries with keys: index, x, y, radius, heading_change, name.
    """

    # Preferred: use official circuit corner metadata
    if session is not None:
        try:
            circuit_info = session.get_circuit_info()
            corners = getattr(circuit_info, "corners", None)
            if corners is not None and not corners.empty:
                turns: List[Dict] = []
                for _, row in corners.iterrows():
                    number = int(row["Number"]) if not pd.isna(row.get("Number")) else len(turns) + 1
                    name = f"Turn {number}"
                    turns.append(
                        {
                            "index": number,
                            "x": float(row["X"]),
                            "y": float(row["Y"]),
                            "radius": float(row.get("Radius", np.nan)) if "Radius" in row else np.nan,
                            "heading_change": float(row.get("Angle", np.nan)) if "Angle" in row else np.nan,
                            "name": name,
                        }
                    )
                return turns
        except Exception as e:
            print(f"Warning: Could not load circuit corner data, falling back to detection: {e}")

    # Fallback: heuristic detection from track geometry
    return _infer_turns_from_track(track_coords if track_coords is not None else np.array([]))


def compute_top_speeds(telemetry_dict: Dict[str, pd.DataFrame]) -> Dict:
    """
    Calculate top speeds from telemetry data for all drivers.

    Args:
        telemetry_dict: Dictionary mapping driver codes to telemetry DataFrames.
            Each DataFrame should have a 'Speed' column in km/h.

    Returns:
        Dictionary containing:
        - per_driver: Dict mapping driver code to their max speed (float, km/h)
        - overall_max: Maximum speed across all drivers (float, km/h)
        - overall_max_driver: Driver code who achieved overall max (str)

    Example:
        >>> telemetry = {
        ...     "VER": extract_driver_telemetry(session, "VER"),
        ...     "HAM": extract_driver_telemetry(session, "HAM")
        ... }
        >>> speeds = compute_top_speeds(telemetry)
        >>> print(f"Fastest: {speeds['overall_max_driver']} at {speeds['overall_max']:.1f} km/h")
    """
    per_driver = {}
    overall_max = 0.0
    overall_max_driver = None

    for driver_code, telemetry in telemetry_dict.items():
        if telemetry.empty or "Speed" not in telemetry.columns:
            continue

        # Get max speed for this driver
        max_speed = telemetry["Speed"].max()

        if pd.notna(max_speed):
            per_driver[driver_code] = float(max_speed)

            # Check if this is the overall maximum
            if max_speed > overall_max:
                overall_max = float(max_speed)
                overall_max_driver = driver_code

    return {
        "per_driver": per_driver,
        "overall_max": overall_max,
        "overall_max_driver": overall_max_driver,
    }


def get_track_coordinates(session: fastf1.core.Session) -> np.ndarray:
    """
    Extract track coordinates from a session's fastest lap.

    Args:
        session: A loaded FastF1 Session object.

    Returns:
        Numpy array of shape (N, 2) with [X, Y] track coordinates in meters.

    Example:
        >>> session = load_session(2024, 5, "R")
        >>> coords = get_track_coordinates(session)
        >>> print(f"Track has {len(coords)} coordinate points")
    """
    # Get the fastest lap to use as track reference
    fastest_lap = session.laps.pick_fastest()

    if fastest_lap is None or fastest_lap.empty:
        raise ValueError("No laps available to extract track coordinates")

    # Get telemetry from fastest lap
    telemetry = fastest_lap.get_telemetry()

    if "X" not in telemetry.columns or "Y" not in telemetry.columns:
        raise ValueError("Telemetry does not contain X/Y coordinates")

    # Extract X, Y coordinates
    coords = telemetry[["X", "Y"]].dropna().values

    return coords
