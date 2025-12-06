# F1 Pit Stop 🏎️

**Interactive Formula 1 Dashboard for New Viewers**

An interactive visualization and data analysis tool for Formula 1 races, designed to help new viewers understand the sport through real-time telemetry replay, track visualization, and detailed driver information.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### 🏁 Interactive Track Replay

- **Visual Track Map**: Automatically rendered circuit layout using GPS telemetry data
- **Real-time Driver Positions**: Each driver shown as a colored dot moving around the track
- **Tyre Strategy Visualization**: Color-coded tyre compounds (Soft/Medium/Hard/Wet/Intermediate)
- **Turn Detection**: Automatic detection and numbering of track corners
- **Sector Boundaries**: Visual representation of track sectors

### 📊 Telemetry & Data

- **Live Telemetry**: Speed, gear, throttle, brake, lap time for each driver
- **Top Speed Tracking**: Circuit-wide and per-driver maximum speeds
- **Compound Analysis**: Real-time tyre compound tracking throughout the session
- **Gap Analysis**: Lap delta to leader and position tracking

### 🎮 Interactive Controls

- **Play/Pause**: Control replay flow
- **Speed Control**: Adjustable replay speed (0.25x to 8x)
- **Step Through**: Frame-by-frame navigation (forward/backward)
- **Jump to Time**: Seek to any point in the session
- **Driver Focus**: Highlight and follow specific drivers

### 🆕 New Viewer Friendly

- **Help Overlay**: In-app guide explaining F1 terminology
- **Tyre Compound Explanations**: Clear descriptions of each compound's characteristics
- **Color-Coded Legend**: Easy-to-understand driver and tyre indicators
- **Tooltips**: Contextual information throughout the interface

### 🌐 API Server (Optional)

- **REST API**: FastAPI-based endpoints for session data
- **JSON Telemetry**: Access processed telemetry programmatically
- **Track Data Export**: Circuit coordinates and turn information
- **CORS Enabled**: Ready for web-based frontends

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- At least 2GB free disk space for telemetry cache

### Step-by-Step Setup

1. **Clone or Download the Repository**

```powershell
cd C:\Users\drket\OneDrive\Desktop\Codes\F1PitStop
```

2. **Create a Virtual Environment (Recommended)**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install Dependencies**

```powershell
pip install -r requirements.txt
```

4. **Configure Environment Variables**

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env and set your cache directory (optional)
# Default cache location: ./cache
```

### Configuration

Create a `.env` file in the project root (or copy from `.env.example`):

```env
# FastF1 cache directory (required to avoid repeated downloads)
FASTF1_CACHE=./cache

# FastF1 credentials (optional, only if needed for certain data)
FASTF1_USERNAME=
FASTF1_PASSWORD=

# Telemetry processing configuration
TELEMETRY_FREQUENCY_HZ=10

# Turn detection threshold (degrees of heading change)
TURN_DETECTION_THRESHOLD=15

# Replay settings
DEFAULT_SPEED_MULTIPLIER=1.0
```

## Quick Start

### Run Interactive Replay (Arcade Mode)

Play the 2024 Australian Grand Prix race:

```powershell
python app.py --year 2024 --gp 3 --session R
```

Play Monaco qualifying:

```powershell
python app.py --year 2024 --gp Monaco --session Q
```

Focus on specific drivers with higher telemetry frequency:

```powershell
python app.py --year 2024 --gp 5 --session R --drivers VER HAM LEC --hz 20
```

### Start API Server

```powershell
python app.py --mode api
```

Access the API documentation at: `http://localhost:8000/docs`

Or start with uvicorn directly:

```powershell
uvicorn api.server:app --reload
```

### Using the Replay Interface

**Keyboard Controls:**

- `SPACE` - Play/Pause
- `←` / `→` - Step backward/forward (1 second)
- `↑` / `↓` - Increase/decrease playback speed
- `H` - Toggle help overlay
- `T` - Toggle telemetry display
- `1-9` - Focus on specific driver (by position in legend)
- `0` - Reset focus to all drivers

## Project Structure

```
F1PitStop/
├── app.py                  # Main entry point (CLI)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
├── .gitignore             # Git ignore rules
│
├── data/                  # Data loading & processing
│   ├── __init__.py
│   ├── loader.py          # FastF1 session loader
│   └── telemetry.py       # Telemetry processing & analysis
│
├── visual/                # Visualization components
│   ├── __init__.py
│   └── arcade_replay.py   # Arcade-based replay window
│
├── api/                   # REST API (optional)
│   ├── __init__.py
│   └── server.py          # FastAPI server
│
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── colors.py          # Color mapping for drivers/tyres
│   └── config.py          # Configuration management
│
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_turn_detection.py
│   └── test_interpolation.py
│
├── .github/
│   └── workflows/
│       └── python-app.yml # GitHub Actions CI/CD
│
└── cache/                 # FastF1 data cache (auto-created)
```

## Command-Line Reference

### Main Application (`app.py`)

```
python app.py [options]

Options:
  --mode {arcade,api}       Run mode: 'arcade' for visualization or 'api' for server (default: arcade)
  --year YEAR              Season year (default: 2024)
  --gp GP                  Grand Prix round number or name (default: 5)
  --session {FP1,FP2,FP3,Q,S,SQ,R}
                           Session type (default: R)
  --drivers DRIVER [DRIVER ...]
                           Specific driver codes to include (e.g., VER HAM LEC)
  --hz HZ                  Telemetry resampling frequency in Hz (default: 10)
  --host HOST              API server host (default: 0.0.0.0)
  --port PORT              API server port (default: 8000)
```

### Session Types

- `FP1`, `FP2`, `FP3` - Free Practice sessions
- `Q` - Qualifying
- `S` - Sprint Race
- `SQ` - Sprint Qualifying
- `R` - Race (Main Event)

### Examples

```powershell
# Play 2024 Monaco GP Race
python app.py --year 2024 --gp Monaco --session R

# Start API server on custom port
python app.py --mode api --port 8080

# Replay with only top 3 drivers at high frequency
python app.py --year 2024 --gp 1 --session R --drivers VER PER HAM --hz 20
```

## API Documentation

### Available Endpoints

When running in API mode, the following endpoints are available:

#### Session Information

```
GET /api/session/{year}/{gp}/{session}
```

Returns session metadata including event name, circuit, date, and participating drivers.

**Example:**

```bash
curl http://localhost:8000/api/session/2024/5/R
```

#### Driver List

```
GET /api/session/{year}/{gp}/{session}/drivers
```

Returns array of driver codes who participated in the session.

#### Driver Telemetry

```
GET /api/session/{year}/{gp}/{session}/telemetry/{driver}?resample_hz=10
```

Returns detailed telemetry for a specific driver.

**Example:**

```bash
curl http://localhost:8000/api/session/2024/5/R/telemetry/VER?resample_hz=10
```

#### Track Information

```
GET /api/session/{year}/{gp}/{session}/track
```

Returns track coordinates and detected turn information.

#### Complete Replay Data

```
GET /api/session/{year}/{gp}/{session}/replay?hz=10&drivers=VER,HAM
```

Returns all data needed for replay visualization (optimized endpoint).

**Example:**

```bash
curl "http://localhost:8000/api/session/2024/5/R/replay?hz=10&drivers=VER,HAM,LEC"
```

### Interactive API Docs

Visit `http://localhost:8000/docs` for interactive Swagger documentation.

## Understanding F1 Terminology

### Tyre Compounds

- **Soft (Red)**: Fastest but wears out quickly - used for short stints and qualifying
- **Medium (Yellow)**: Balanced performance and durability
- **Hard (White)**: Slowest but lasts longest - used for long race stints
- **Intermediate (Green)**: For light rain conditions
- **Wet (Blue)**: For heavy rain with significant standing water

### Track Elements

- **Turns/Corners**: Numbered points where the track curves significantly
- **Sectors**: Track divided into 3 sections for timing analysis
- **Lap Time**: Time to complete one full circuit
- **Delta**: Time difference compared to another lap or driver

### Telemetry Data

- **Speed**: Current velocity in km/h
- **Gear**: Current transmission gear (1-8)
- **Throttle**: Accelerator input (0-100%)
- **Brake**: Brake pressure (0-100%)
- **DRS**: Drag Reduction System (rear wing opens for more speed)

## Development

### Running Tests

Run all tests:

```powershell
pytest tests/ -v
```

Run specific test file:

```powershell
pytest tests/test_turn_detection.py -v
```

Run with coverage:

```powershell
pytest tests/ --cov=. --cov-report=html
```

### Code Structure Guidelines

**Adding New Features:**

1. **Data Processing**: Add functions to `data/telemetry.py`
2. **Visualization**: Modify `visual/arcade_replay.py`
3. **API Endpoints**: Add to `api/server.py`
4. **Configuration**: Update `utils/config.py` and `.env.example`

**Function Contracts:**

- Use type hints for all function parameters and return values
- Include comprehensive docstrings with Args, Returns, and Examples
- Handle errors gracefully with informative messages

**Testing:**

- Add unit tests for new algorithms in `tests/`
- Test edge cases (empty data, missing values, etc.)
- Use synthetic data for reproducible tests

### Turn Detection Algorithm

The turn detection algorithm (`compute_turns()`) uses heading change analysis:

1. **Compute Tangent Vectors**: Calculate direction vectors between consecutive GPS points
2. **Calculate Heading**: Use `arctan2(dy, dx)` to get angle of each segment
3. **Detect Heading Changes**: Find where heading changes exceed threshold
4. **Merge Nearby Detections**: Combine closely-spaced detections into single corners
5. **Estimate Radius**: Calculate turn radius from arc length and heading change

**Tuning Parameters:**

- `TURN_DETECTION_THRESHOLD`: Default 15° (adjust in `.env`)
  - Lower (10-12°) for tight circuits like Monaco
  - Higher (20-25°) for fast circuits like Monza
- Merge distance: Default 50m (modify in `telemetry.py`)

### Telemetry Interpolation

The `build_common_timebase()` function resamples all drivers to a shared timeline:

1. Find global time range across all drivers
2. Create uniform time grid at specified frequency (Hz)
3. Interpolate continuous values (speed, position) using linear interpolation
4. Use nearest-neighbor for discrete values (gear, lap number)
5. Forward-fill tyre compounds (changes only at pit stops)

**Performance Considerations:**

- Lower Hz (5) for better performance
- Higher Hz (20) for smoother visualization
- Default 10 Hz is a good balance

## Troubleshooting

### FastF1 Download Issues

**Problem**: Session fails to load or takes very long

```
Failed to load session 2024/5/R. Error: ...
```

**Solutions:**

1. Check internet connection
2. Verify the GP number/name and session type are correct
3. Ensure `FASTF1_CACHE` directory has write permissions
4. Some older sessions may have limited data availability

### Missing Telemetry Data

**Problem**: Some drivers appear missing or incomplete

**Reasons:**

- Driver retired from the session (mechanical failure, crash)
- Telemetry data not available for that session
- Driver participated only briefly (reserve driver)

**Solution**: This is normal - the system handles missing data gracefully

### Arcade Window Issues

**Problem**: Window doesn't open or crashes

**Solutions:**

1. Ensure you have a graphics driver installed
2. Try updating Python Arcade: `pip install --upgrade arcade`
3. Check that you're not running in a headless environment (requires display)

### Performance Issues

**Problem**: Replay is choppy or slow

**Solutions:**

1. Reduce telemetry frequency: `--hz 5`
2. Limit drivers: `--drivers VER HAM LEC`
3. Close other applications
4. Use a faster computer or reduce window size

## Contributing

Contributions are welcome! Areas for improvement:

- **Pit Stop Analysis**: Detect and visualize pit stops
- **Race Strategy**: Predict optimal tyre strategies
- **Weather Integration**: Include weather data in replay
- **Comparative Analysis**: Side-by-side driver comparison
- **3D Visualization**: Three-dimensional track rendering
- **Live Timing**: Real-time race following during live events
- **Mobile App**: React Native or Flutter frontend using the API

## License

This project is provided as-is for educational purposes. Formula 1 data is property of Formula One Management and used via the FastF1 library for non-commercial purposes.

## Acknowledgments

- **FastF1**: Python library for accessing F1 data ([GitHub](https://github.com/theOehrly/Fast-F1))
- **Arcade**: Python game framework used for visualization ([Arcade Library](https://api.arcade.academy/))
- **Formula 1**: For providing the exciting sport we're visualizing

## Support

For issues, questions, or suggestions:

1. Check this README first
2. Review existing GitHub issues
3. Create a new issue with detailed description
4. Include error messages and steps to reproduce

---

**Built with ❤️ for F1 fans and data enthusiasts**

Enjoy exploring Formula 1 data in a whole new way! 🏎️💨
