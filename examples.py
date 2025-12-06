"""
Simple example script to demonstrate F1 Pit Stop usage.

This script shows how to use the library programmatically instead of via CLI.
"""

from data.loader import load_session, get_session_info
from data.telemetry import (
    extract_driver_telemetry,
    build_common_timebase,
    compute_turns,
    compute_top_speeds,
    get_track_coordinates,
)
from visual.arcade_replay import F1ReplayWindow
import arcade


def example_load_and_analyze():
    """
    Example: Load a session and print statistics without visualization.
    """
    print("=" * 60)
    print("Example 1: Load and Analyze Session")
    print("=" * 60)
    
    # Load the 2024 Monaco GP Race
    print("\nLoading 2024 Monaco GP Race...")
    session = load_session(2024, "Monaco", "R")
    
    # Get session information
    info = get_session_info(session)
    print(f"\nEvent: {info['event_name']}")
    print(f"Circuit: {info['circuit_name']}")
    print(f"Date: {info['date']}")
    print(f"Total Laps: {info['total_laps']}")
    print(f"Drivers: {', '.join(info['drivers'][:5])}... (and {len(info['drivers']) - 5} more)")
    
    # Get track coordinates and detect turns
    print("\nAnalyzing track...")
    track_coords = get_track_coordinates(session)
    turns = compute_turns(track_coords)
    print(f"Track has {len(track_coords)} GPS points")
    print(f"Detected {len(turns)} turns")
    
    # Extract telemetry for top 3 drivers
    print("\nExtracting telemetry for VER, HAM, LEC...")
    telemetry_dict = {}
    for driver in ["VER", "HAM", "LEC"]:
        try:
            telemetry_dict[driver] = extract_driver_telemetry(session, driver)
            print(f"  {driver}: {len(telemetry_dict[driver])} telemetry points")
        except Exception as e:
            print(f"  {driver}: Could not load - {e}")
    
    # Compute top speeds
    if telemetry_dict:
        speeds = compute_top_speeds(telemetry_dict)
        print(f"\nTop Speeds:")
        for driver, speed in speeds['per_driver'].items():
            print(f"  {driver}: {speed:.1f} km/h")
        print(f"\nFastest: {speeds['overall_max_driver']} at {speeds['overall_max']:.1f} km/h")


def example_simple_replay():
    """
    Example: Load a recent session and launch replay with minimal code.
    """
    print("\n" + "=" * 60)
    print("Example 2: Simple Replay Launch")
    print("=" * 60)
    
    # Configure session
    year = 2024
    gp = 5  # Round 5
    session_type = "R"  # Race
    
    print(f"\nLoading {year} Round {gp} {session_type}...")
    
    # Load session
    session = load_session(year, gp, session_type)
    session_info = get_session_info(session)
    
    # Get track
    track_coords = get_track_coordinates(session)
    turns = compute_turns(track_coords)
    
    # Extract telemetry for a few drivers
    drivers_to_show = ["VER", "HAM", "LEC"]  # Modify as needed
    telemetry_dict = {}
    
    for driver in drivers_to_show:
        try:
            telemetry_dict[driver] = extract_driver_telemetry(session, driver)
        except Exception as e:
            print(f"Warning: Could not load {driver}: {e}")
    
    if not telemetry_dict:
        print("No telemetry loaded. Exiting.")
        return
    
    # Build common timebase
    timeline = build_common_timebase(telemetry_dict, hz=10)
    
    # Compute statistics
    top_speeds = compute_top_speeds(telemetry_dict)
    
    # Launch visualization
    print("\nLaunching replay window...")
    print("Press H in the window for help")
    
    window = F1ReplayWindow(
        width=1400,
        height=900,
        track_coords=track_coords,
        drivers=telemetry_dict,
        timeline=timeline,
        turns=turns,
        session_info=session_info,
        top_speeds=top_speeds,
    )
    
    arcade.run()


def example_api_usage():
    """
    Example: How to use the API programmatically (not via HTTP).
    """
    print("\n" + "=" * 60)
    print("Example 3: Direct API Module Usage")
    print("=" * 60)
    
    from api.server import get_or_load_session
    
    # Load via API cache
    print("\nLoading session via API cache...")
    session_data = get_or_load_session(2024, 5, "R")
    
    info = session_data["info"]
    print(f"\nLoaded: {info['event_name']}")
    print(f"Drivers: {len(info['drivers'])}")
    
    # Access the FastF1 session object
    session = session_data["session"]
    print(f"Session type: {session.name}")


if __name__ == "__main__":
    import sys
    
    print("F1 Pit Stop - Usage Examples")
    print("Choose an example to run:")
    print("1. Load and analyze (no GUI)")
    print("2. Simple replay launch")
    print("3. API module usage")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-3): ").strip()
    
    try:
        if choice == "1":
            example_load_and_analyze()
        elif choice == "2":
            example_simple_replay()
        elif choice == "3":
            example_api_usage()
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
