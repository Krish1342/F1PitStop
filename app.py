"""
F1 Pit Stop - Interactive Formula 1 Dashboard for New Viewers

Main application entry point with CLI support for both Arcade visualization
and FastAPI server modes.
"""

import argparse
import sys
from typing import Optional

from data.loader import load_session, get_session_info
from data.telemetry import (
    extract_driver_telemetry,
    build_common_timebase,
    compute_turns,
    compute_top_speeds,
    get_track_coordinates,
)
from visual.arcade_replay import F1ReplayWindow
from utils.config import config


def run_arcade_replay(
    year: int,
    gp: int,
    session_type: str = "R",
    drivers: Optional[list] = None,
    hz: int = None
):
    """
    Load session data and launch the Arcade replay window.
    
    Args:
        year: Season year (e.g., 2024).
        gp: Grand Prix round number.
        session_type: Session type (R, Q, etc.).
        drivers: Optional list of driver codes to include. If None, includes all.
        hz: Telemetry resampling frequency. If None, uses config default.
    """
    print("=" * 60)
    print("F1 Pit Stop - Interactive Replay")
    print("=" * 60)
    
    # Use config frequency if not specified
    if hz is None:
        hz = config.telemetry_frequency
    
    # Step 1: Load session
    print(f"\n[1/6] Loading session: {year} Round {gp} ({session_type})")
    session = load_session(year, gp, session_type)
    session_info = get_session_info(session)
    
    print(f"  ✓ Loaded: {session_info['event_name']} - {session_info['session_name']}")
    print(f"  ✓ Circuit: {session_info['circuit_name']}")
    print(f"  ✓ Drivers: {len(session_info['drivers'])}")
    
    # Step 2: Get track coordinates
    print("\n[2/6] Extracting track coordinates...")
    track_coords = get_track_coordinates(session)
    print(f"  ✓ Track points: {len(track_coords)}")
    
    # Step 3: Detect turns
    print("\n[3/6] Detecting turns...")
    turns = compute_turns(track_coords, session=session)
    print(f"  ✓ Detected {len(turns)} turns")
    
    # Step 4: Extract driver telemetry
    print(f"\n[4/6] Extracting telemetry for drivers...")
    
    # Determine which drivers to include
    if drivers:
        driver_list = [d.upper() for d in drivers]
    else:
        driver_list = session_info['drivers']
    
    telemetry_dict = {}
    for driver_code in driver_list:
        try:
            print(f"  - Loading {driver_code}...", end=" ")
            telemetry = extract_driver_telemetry(session, driver_code)
            telemetry_dict[driver_code] = telemetry
            print(f"✓ ({len(telemetry)} samples)")
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    if not telemetry_dict:
        print("\n✗ Error: No telemetry data loaded. Cannot start replay.")
        return
    
    print(f"  ✓ Loaded telemetry for {len(telemetry_dict)} drivers")
    
    # Step 5: Build common timebase
    print(f"\n[5/6] Building common timebase at {hz} Hz...")
    timeline = build_common_timebase(telemetry_dict, hz=hz)
    print(f"  ✓ Timeline: {len(timeline)} samples ({timeline[-1] - timeline[0]:.1f} seconds)")
    
    # Step 6: Compute top speeds
    print("\n[6/6] Computing statistics...")
    top_speeds = compute_top_speeds(telemetry_dict)
    if top_speeds['overall_max_driver']:
        print(f"  ✓ Top speed: {top_speeds['overall_max']:.1f} km/h ({top_speeds['overall_max_driver']})")
    
    # Launch Arcade window
    print("\n" + "=" * 60)
    print("Launching replay window...")
    print("=" * 60)
    print("\nControls:")
    print("  SPACE       - Play/Pause")
    print("  ← / →       - Step backward/forward")
    print("  ↑ / ↓       - Increase/decrease speed")
    print("  H           - Toggle help overlay")
    print("  T           - Toggle telemetry display")
    print("  1-9         - Focus on specific driver")
    print("  0           - Reset focus")
    print("\nPress H in the window for detailed help")
    print("=" * 60 + "\n")
    
    # Create and run window
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
    
    import arcade
    arcade.run()


def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the FastAPI server.
    
    Args:
        host: Host address to bind to.
        port: Port number to listen on.
    """
    print("=" * 60)
    print("F1 Pit Stop - API Server")
    print("=" * 60)
    print(f"\nStarting server on {host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")
    print(f"Health check: http://{host}:{port}/api/health")
    print("\nExample endpoints:")
    print(f"  http://{host}:{port}/api/session/2024/5/R")
    print(f"  http://{host}:{port}/api/session/2024/5/R/replay")
    print("=" * 60 + "\n")
    
    import uvicorn
    from api.server import app
    
    uvicorn.run(app, host=host, port=port)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="F1 Pit Stop - Interactive Formula 1 Dashboard for New Viewers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Play 2024 Australian GP race (round 3)
  python app.py --year 2024 --gp 3 --session R
  
  # Play 2024 Monaco GP qualifying
  python app.py --year 2024 --gp Monaco --session Q
  
  # Start API server
  python app.py --mode api
  
  # Play with only specific drivers at higher frequency
  python app.py --year 2024 --gp 5 --session R --drivers VER HAM LEC --hz 20
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["arcade", "api"],
        default="arcade",
        help="Run mode: 'arcade' for visualization or 'api' for server (default: arcade)"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Season year (default: 2024)"
    )
    
    parser.add_argument(
        "--gp",
        default=5,
        help="Grand Prix round number or name (default: 5)"
    )
    
    parser.add_argument(
        "--session",
        choices=["FP1", "FP2", "FP3", "Q", "S", "SQ", "R"],
        default="R",
        help="Session type: FP1, FP2, FP3, Q (Qualifying), S (Sprint), SQ (Sprint Qualifying), R (Race) (default: R)"
    )
    
    parser.add_argument(
        "--drivers",
        nargs="+",
        help="Specific driver codes to include (e.g., VER HAM LEC). If not specified, includes all drivers."
    )
    
    parser.add_argument(
        "--hz",
        type=int,
        help=f"Telemetry resampling frequency in Hz (default: {config.telemetry_frequency})"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Convert gp to int if it's a number
    try:
        gp = int(args.gp)
    except ValueError:
        gp = args.gp
    
    # Run in selected mode
    try:
        if args.mode == "arcade":
            run_arcade_replay(
                year=args.year,
                gp=gp,
                session_type=args.session,
                drivers=args.drivers,
                hz=args.hz
            )
        elif args.mode == "api":
            run_api_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n\nShutdown requested... exiting")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
