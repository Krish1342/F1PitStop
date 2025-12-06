"""
FastAPI server for F1 session data.

This module provides REST API endpoints to access F1 session metadata,
telemetry data, and replay information via HTTP.
"""

from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from data.loader import load_session, get_session_info
from data.telemetry import (
    extract_driver_telemetry,
    build_common_timebase,
    compute_turns,
    compute_top_speeds,
    get_track_coordinates,
)


# Initialize FastAPI app
app = FastAPI(
    title="F1 Pit Stop API",
    description="REST API for Formula 1 session data, telemetry, and replay visualization",
    version="1.0.0",
)

# Enable CORS for browser-based clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for loaded sessions
# Key: (year, gp, session_type)
session_cache: Dict[tuple, dict] = {}


def get_or_load_session(year: int, gp: Union[str, int], session_type: str) -> dict:
    """
    Get a session from cache or load it if not cached.

    Args:
        year: Year of the session.
        gp: Grand Prix number or name.
        session_type: Session type (R, Q, etc.).

    Returns:
        Dictionary containing session data and metadata.
    """
    cache_key = (year, str(gp), session_type)

    if cache_key not in session_cache:
        # Load session
        session = load_session(year, gp, session_type)

        # Extract metadata
        session_info = get_session_info(session)

        # Cache the session object and metadata
        session_cache[cache_key] = {
            "session": session,
            "info": session_info,
        }

    return session_cache[cache_key]


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "F1 Pit Stop API",
        "version": "1.0.0",
        "description": "Interactive F1 dashboard API for new viewers",
        "endpoints": {
            "session_info": "/api/session/{year}/{gp}/{session}",
            "telemetry": "/api/session/{year}/{gp}/{session}/telemetry/{driver}",
            "replay": "/api/session/{year}/{gp}/{session}/replay",
            "track": "/api/session/{year}/{gp}/{session}/track",
            "drivers": "/api/session/{year}/{gp}/{session}/drivers",
        },
    }


@app.get("/api/session/{year}/{gp}/{session}")
async def get_session_metadata(year: int, gp: Union[str, int], session: str = "R"):
    """
    Get session metadata including event name, circuit, date, and drivers.

    Args:
        year: Season year (e.g., 2024).
        gp: Grand Prix round number or name.
        session: Session type (FP1, FP2, FP3, Q, S, SQ, R).

    Returns:
        JSON object with session information.

    Example:
        GET /api/session/2024/5/R
    """
    try:
        session_data = get_or_load_session(year, gp, session)
        return session_data["info"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{year}/{gp}/{session}/drivers")
async def get_session_drivers(year: int, gp: Union[str, int], session: str = "R"):
    """
    Get list of drivers who participated in the session.

    Returns:
        JSON array of driver codes.

    Example:
        GET /api/session/2024/5/R/drivers
        Response: ["VER", "HAM", "LEC", ...]
    """
    try:
        session_data = get_or_load_session(year, gp, session)
        return session_data["info"]["drivers"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{year}/{gp}/{session}/telemetry/{driver}")
async def get_driver_telemetry(
    year: int,
    gp: Union[str, int],
    session: str,
    driver: str,
    resample_hz: Optional[int] = Query(None, description="Resample frequency in Hz"),
):
    """
    Get telemetry data for a specific driver.

    Args:
        year: Season year.
        gp: Grand Prix round number or name.
        session: Session type.
        driver: Three-letter driver code (e.g., "VER").
        resample_hz: Optional resampling frequency in Hz.

    Returns:
        JSON object with telemetry data.

    Example:
        GET /api/session/2024/5/R/telemetry/VER?resample_hz=10
    """
    try:
        session_data = get_or_load_session(year, gp, session)
        f1_session = session_data["session"]

        # Extract telemetry
        telemetry = extract_driver_telemetry(f1_session, driver)

        # Optionally resample
        if resample_hz:
            telemetry_dict = {driver: telemetry}
            build_common_timebase(telemetry_dict, hz=resample_hz)
            telemetry = telemetry_dict[driver]

        # Convert to JSON-serializable format
        result = telemetry.to_dict(orient="records")

        return {"driver": driver, "sample_count": len(result), "telemetry": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{year}/{gp}/{session}/track")
async def get_track_info(year: int, gp: Union[str, int], session: str = "R"):
    """
    Get track information including coordinates and detected turns.

    Returns:
        JSON object with track coordinates and turn data.

    Example:
        GET /api/session/2024/5/R/track
    """
    try:
        session_data = get_or_load_session(year, gp, session)
        f1_session = session_data["session"]

        # Get track coordinates
        track_coords = get_track_coordinates(f1_session)

        # Detect turns (prefer official corner data)
        turns = compute_turns(track_coords, session=f1_session)

        return {
            "coordinates": track_coords.tolist(),
            "turns": turns,
            "turn_count": len(turns),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{year}/{gp}/{session}/replay")
async def get_replay_data(
    year: int,
    gp: Union[str, int],
    session: str = "R",
    hz: int = Query(10, description="Telemetry frequency in Hz"),
    drivers: Optional[str] = Query(None, description="Comma-separated driver codes"),
):
    """
    Get precomputed replay data for visualization.

    This endpoint returns all data needed for replay visualization including
    track coordinates, driver telemetry (resampled to common timebase),
    turn locations, and top speeds.

    Args:
        year: Season year.
        gp: Grand Prix round number or name.
        session: Session type.
        hz: Telemetry resampling frequency (default: 10 Hz).
        drivers: Optional comma-separated list of driver codes to include.

    Returns:
        JSON object with complete replay data.

    Example:
        GET /api/session/2024/5/R/replay?hz=10&drivers=VER,HAM,LEC
    """
    try:
        session_data = get_or_load_session(year, gp, session)
        f1_session = session_data["session"]
        session_info = session_data["info"]

        # Determine which drivers to include
        if drivers:
            driver_list = [d.strip().upper() for d in drivers.split(",")]
        else:
            driver_list = session_info["drivers"]

        # Get track coordinates
        track_coords = get_track_coordinates(f1_session)

        # Detect turns (prefer official corner data)
        turns = compute_turns(track_coords, session=f1_session)

        # Extract telemetry for all drivers
        telemetry_dict = {}
        for driver_code in driver_list:
            try:
                telemetry = extract_driver_telemetry(f1_session, driver_code)
                telemetry_dict[driver_code] = telemetry
            except Exception as e:
                print(f"Warning: Could not load telemetry for {driver_code}: {e}")

        # Build common timebase
        timeline = build_common_timebase(telemetry_dict, hz=hz)

        # Compute top speeds
        top_speeds = compute_top_speeds(telemetry_dict)

        # Convert telemetry to JSON format
        telemetry_json = {}
        for driver_code, telemetry in telemetry_dict.items():
            telemetry_json[driver_code] = telemetry.to_dict(orient="records")

        return {
            "session_info": session_info,
            "track_coordinates": track_coords.tolist(),
            "turns": turns,
            "timeline": timeline.tolist(),
            "telemetry": telemetry_json,
            "top_speeds": top_speeds,
            "sample_frequency_hz": hz,
            "sample_count": len(timeline),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "cached_sessions": len(session_cache)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
