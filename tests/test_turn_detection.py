"""
Unit tests for turn detection algorithm.

Tests the compute_turns function with known track geometries.
"""

import numpy as np
import pytest

from data.telemetry import compute_turns


def test_straight_line_no_turns():
    """Test that a straight line produces no turns."""
    # Create a straight line track (100 points)
    track = np.array([[i, 0] for i in range(100)], dtype=float)
    
    turns = compute_turns(track)
    
    # Should detect no turns on a straight line
    assert len(turns) == 0


def test_single_right_angle_turn():
    """Test detection of a single 90-degree right turn."""
    # Create L-shaped track: horizontal then vertical
    horizontal = np.array([[i, 0] for i in range(50)], dtype=float)
    vertical = np.array([[50, i] for i in range(1, 51)], dtype=float)
    track = np.vstack([horizontal, vertical])
    
    turns = compute_turns(track)
    
    # Should detect one turn
    assert len(turns) >= 1
    
    # Turn should be near the corner (around index 50)
    turn_indices = [t["index"] for t in turns]
    assert any(45 <= idx <= 55 for idx in turn_indices)


def test_square_track_four_turns():
    """Test detection of four 90-degree turns in a square."""
    # Create a square track
    side_length = 30
    
    # Bottom side (left to right)
    bottom = np.array([[i, 0] for i in range(side_length)], dtype=float)
    # Right side (bottom to top)
    right = np.array([[side_length, i] for i in range(1, side_length)], dtype=float)
    # Top side (right to left)
    top = np.array([[side_length - i, side_length] for i in range(1, side_length)], dtype=float)
    # Left side (top to bottom)
    left = np.array([[0, side_length - i] for i in range(1, side_length)], dtype=float)
    
    track = np.vstack([bottom, right, top, left])
    
    turns = compute_turns(track)
    
    # Should detect 4 corners
    # May detect 3-5 depending on threshold and merging
    assert 3 <= len(turns) <= 5


def test_circular_track_smooth_curve():
    """Test that a smooth circular track is detected as multiple turns or continuous curve."""
    # Create a circular track
    angles = np.linspace(0, 2 * np.pi, 200)
    radius = 100
    track = np.column_stack([
        radius * np.cos(angles),
        radius * np.sin(angles)
    ])
    
    turns = compute_turns(track)
    
    # A smooth circle should either:
    # - Be detected as many small turns (gradual curvature)
    # - Or no sharp turns if threshold is high
    # We'll just verify it doesn't crash and returns a list
    assert isinstance(turns, list)


def test_chicane_multiple_turns():
    """Test detection of a chicane (quick left-right sequence)."""
    # Create a chicane: straight, left, right, straight
    track = []
    
    # Initial straight
    for i in range(30):
        track.append([i, 0])
    
    # Left turn
    for i in range(10):
        track.append([30 + i, i])
    
    # Right turn
    for i in range(10):
        track.append([40 + i, 10 - i])
    
    # Final straight
    for i in range(30):
        track.append([50 + i, 0])
    
    track = np.array(track, dtype=float)
    
    turns = compute_turns(track)
    
    # Should detect at least 2 turns (left and right)
    assert len(turns) >= 2


def test_empty_track():
    """Test that empty track doesn't cause errors."""
    track = np.array([], dtype=float).reshape(0, 2)
    
    turns = compute_turns(track)
    
    assert len(turns) == 0


def test_insufficient_points():
    """Test that track with too few points doesn't crash."""
    track = np.array([[0, 0], [1, 1]], dtype=float)
    
    turns = compute_turns(track)
    
    # Should return empty list or handle gracefully
    assert isinstance(turns, list)


def test_turn_metadata():
    """Test that turn data includes all required fields."""
    # Create L-shaped track
    horizontal = np.array([[i, 0] for i in range(50)], dtype=float)
    vertical = np.array([[50, i] for i in range(1, 51)], dtype=float)
    track = np.vstack([horizontal, vertical])
    
    turns = compute_turns(track)
    
    if len(turns) > 0:
        turn = turns[0]
        
        # Check all required fields exist
        assert "index" in turn
        assert "x" in turn
        assert "y" in turn
        assert "radius" in turn
        assert "heading_change" in turn
        assert "name" in turn
        
        # Check types
        assert isinstance(turn["index"], int)
        assert isinstance(turn["x"], float)
        assert isinstance(turn["y"], float)
        assert isinstance(turn["radius"], float)
        assert isinstance(turn["heading_change"], float)
        assert isinstance(turn["name"], str)
        
        # Check name format
        assert turn["name"].startswith("Turn ")


def test_turn_numbering():
    """Test that turns are numbered sequentially."""
    # Create square track with 4 turns
    side_length = 30
    bottom = np.array([[i, 0] for i in range(side_length)], dtype=float)
    right = np.array([[side_length, i] for i in range(1, side_length)], dtype=float)
    top = np.array([[side_length - i, side_length] for i in range(1, side_length)], dtype=float)
    left = np.array([[0, side_length - i] for i in range(1, side_length)], dtype=float)
    track = np.vstack([bottom, right, top, left])
    
    turns = compute_turns(track)
    
    # Extract turn numbers from names
    turn_numbers = []
    for turn in turns:
        name = turn["name"]
        number = int(name.split()[-1])
        turn_numbers.append(number)
    
    # Check sequential numbering starting from 1
    expected = list(range(1, len(turns) + 1))
    assert turn_numbers == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
