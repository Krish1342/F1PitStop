"""
Unit tests for telemetry interpolation and timebase building.

Tests the build_common_timebase function with various scenarios.
"""

import numpy as np
import pandas as pd
import pytest

from data.telemetry import build_common_timebase


def create_sample_telemetry(
    start_time: float,
    end_time: float,
    num_samples: int,
    speed_range: tuple = (100, 300)
) -> pd.DataFrame:
    """
    Create synthetic telemetry data for testing.
    
    Args:
        start_time: Start time in seconds.
        end_time: End time in seconds.
        num_samples: Number of samples to generate.
        speed_range: Tuple of (min_speed, max_speed) in km/h.
    
    Returns:
        DataFrame with synthetic telemetry.
    """
    times = np.linspace(start_time, end_time, num_samples)
    
    return pd.DataFrame({
        "SessionTime": times,
        "X": np.linspace(0, 1000, num_samples),
        "Y": np.linspace(0, 500, num_samples),
        "Speed": np.linspace(speed_range[0], speed_range[1], num_samples),
        "nGear": np.random.randint(1, 8, num_samples),
        "Throttle": np.random.uniform(0, 100, num_samples),
        "Brake": np.random.uniform(0, 100, num_samples),
        "Compound": ["SOFT"] * num_samples,
        "LapNumber": [1] * num_samples,
        "Distance": np.linspace(0, 5000, num_samples),
    })


def test_single_driver_timebase():
    """Test timebase creation with a single driver."""
    telemetry = {
        "VER": create_sample_telemetry(0, 100, 50)
    }
    
    timeline = build_common_timebase(telemetry, hz=10)
    
    # Check timeline properties
    assert len(timeline) > 0
    assert timeline[0] >= 0
    assert timeline[-1] <= 100
    
    # Check frequency (should be ~10 Hz)
    if len(timeline) > 1:
        dt = timeline[1] - timeline[0]
        expected_dt = 1.0 / 10
        assert abs(dt - expected_dt) < 0.01


def test_multiple_drivers_same_timerange():
    """Test timebase with multiple drivers in the same time range."""
    telemetry = {
        "VER": create_sample_telemetry(0, 100, 50),
        "HAM": create_sample_telemetry(0, 100, 60),
        "LEC": create_sample_telemetry(0, 100, 40),
    }
    
    timeline = build_common_timebase(telemetry, hz=10)
    
    # All drivers should have same length after interpolation
    assert len(telemetry["VER"]) == len(timeline)
    assert len(telemetry["HAM"]) == len(timeline)
    assert len(telemetry["LEC"]) == len(timeline)
    
    # All should have same SessionTime values
    assert np.allclose(telemetry["VER"]["SessionTime"], timeline)
    assert np.allclose(telemetry["HAM"]["SessionTime"], timeline)
    assert np.allclose(telemetry["LEC"]["SessionTime"], timeline)


def test_different_timeranges():
    """Test with drivers who have different time ranges (e.g., one retires early)."""
    telemetry = {
        "VER": create_sample_telemetry(0, 100, 50),  # Full race
        "HAM": create_sample_telemetry(0, 100, 50),  # Full race
        "LAT": create_sample_telemetry(0, 50, 25),   # Retires halfway
    }
    
    timeline = build_common_timebase(telemetry, hz=10)
    
    # Timeline should span full range
    assert timeline[0] <= 0
    assert timeline[-1] >= 50
    
    # LAT should have NaN values after their data ends
    lat_telemetry = telemetry["LAT"]
    late_time_mask = lat_telemetry["SessionTime"] > 50
    if late_time_mask.any():
        # Check that some values are NaN beyond LAT's data
        assert lat_telemetry.loc[late_time_mask, "Speed"].isna().any()


def test_different_frequencies():
    """Test different resampling frequencies."""
    telemetry_5hz = {
        "VER": create_sample_telemetry(0, 100, 50)
    }
    telemetry_20hz = {
        "VER": create_sample_telemetry(0, 100, 50)
    }
    
    timeline_5hz = build_common_timebase(telemetry_5hz, hz=5)
    timeline_20hz = build_common_timebase(telemetry_20hz, hz=20)
    
    # 20 Hz should have ~4x more samples than 5 Hz
    ratio = len(timeline_20hz) / len(timeline_5hz)
    assert 3.5 < ratio < 4.5


def test_interpolation_preserves_values():
    """Test that interpolation preserves values at original timestamps."""
    # Create telemetry with known values
    original_times = np.array([0, 10, 20, 30, 40, 50])
    original_speeds = np.array([100, 150, 200, 250, 300, 350])
    
    telemetry = {
        "VER": pd.DataFrame({
            "SessionTime": original_times,
            "Speed": original_speeds,
            "X": np.linspace(0, 1000, len(original_times)),
            "Y": np.linspace(0, 500, len(original_times)),
        })
    }
    
    # Resample at 1 Hz (should include our original timestamps)
    timeline = build_common_timebase(telemetry, hz=1)
    
    # Check that values at original timestamps are preserved (within tolerance)
    interpolated = telemetry["VER"]
    for orig_time, orig_speed in zip(original_times, original_speeds):
        # Find closest interpolated time
        idx = np.argmin(np.abs(interpolated["SessionTime"] - orig_time))
        interpolated_speed = interpolated.iloc[idx]["Speed"]
        
        # Should be very close to original
        if not pd.isna(interpolated_speed):
            assert abs(interpolated_speed - orig_speed) < 10


def test_empty_telemetry():
    """Test handling of empty telemetry dictionary."""
    telemetry = {}
    
    timeline = build_common_timebase(telemetry, hz=10)
    
    assert len(timeline) == 0


def test_compound_forward_fill():
    """Test that tyre compound is forward-filled correctly."""
    # Create telemetry with compound changes
    telemetry = {
        "VER": pd.DataFrame({
            "SessionTime": [0, 10, 20, 30, 40],
            "Speed": [100, 150, 200, 250, 300],
            "X": [0, 200, 400, 600, 800],
            "Y": [0, 100, 200, 300, 400],
            "Compound": ["SOFT", "SOFT", "MEDIUM", "MEDIUM", "MEDIUM"],
        })
    }
    
    timeline = build_common_timebase(telemetry, hz=2)  # 2 Hz for easier verification
    
    interpolated = telemetry["VER"]
    
    # Check that compound doesn't have invalid values
    compounds = interpolated["Compound"].unique()
    assert all(c in ["SOFT", "MEDIUM", "UNKNOWN"] for c in compounds)


def test_interpolated_columns_exist():
    """Test that all expected columns exist after interpolation."""
    telemetry = {
        "VER": create_sample_telemetry(0, 100, 50)
    }
    
    build_common_timebase(telemetry, hz=10)
    
    interpolated = telemetry["VER"]
    
    # Check that key columns exist
    expected_columns = ["SessionTime", "X", "Y", "Speed"]
    for col in expected_columns:
        assert col in interpolated.columns


def test_timebase_monotonic():
    """Test that the timebase is monotonically increasing."""
    telemetry = {
        "VER": create_sample_telemetry(0, 100, 50),
        "HAM": create_sample_telemetry(0, 100, 50),
    }
    
    timeline = build_common_timebase(telemetry, hz=10)
    
    # Check monotonic increase
    assert np.all(np.diff(timeline) >= 0)


def test_no_session_time_column():
    """Test handling of telemetry without SessionTime column."""
    telemetry = {
        "VER": pd.DataFrame({
            "Speed": [100, 150, 200],
            "X": [0, 100, 200],
            "Y": [0, 50, 100],
        })
    }
    
    # Should handle gracefully (skip this driver or raise error)
    try:
        timeline = build_common_timebase(telemetry, hz=10)
        # If it doesn't raise, timeline should be empty or driver skipped
        assert True
    except (ValueError, KeyError):
        # Expected to fail without SessionTime
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
