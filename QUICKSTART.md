# F1 Pit Stop - Quick Reference Guide

## Installation

```powershell
# 1. Navigate to project
cd C:\Users\drket\OneDrive\Desktop\Codes\F1PitStop

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
Copy-Item .env.example .env
```

## Common Commands

### Interactive Replay

```powershell
# Play 2024 Monaco GP Race
python app.py --year 2024 --gp Monaco --session R

# Play Australian GP (Round 3) Qualifying
python app.py --year 2024 --gp 3 --session Q

# Focus on specific drivers
python app.py --year 2024 --gp 5 --session R --drivers VER HAM LEC
```

### API Server

```powershell
# Start server (default port 8000)
python app.py --mode api

# Custom port
python app.py --mode api --port 8080

# Or with uvicorn
uvicorn api.server:app --reload
```

### Testing

```powershell
# Run all tests
pytest

# Run specific test file
pytest tests/test_turn_detection.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Keyboard Controls (Arcade Mode)

| Key     | Action                      |
| ------- | --------------------------- |
| `SPACE` | Play/Pause                  |
| `←`     | Step backward 1 second      |
| `→`     | Step forward 1 second       |
| `↑`     | Increase playback speed     |
| `↓`     | Decrease playback speed     |
| `H`     | Toggle help overlay         |
| `T`     | Toggle telemetry display    |
| `1-9`   | Focus on driver by position |
| `0`     | Reset focus to all drivers  |

## API Endpoints Quick Reference

```bash
# Session info
GET http://localhost:8000/api/session/2024/5/R

# Driver list
GET http://localhost:8000/api/session/2024/5/R/drivers

# Driver telemetry
GET http://localhost:8000/api/session/2024/5/R/telemetry/VER?resample_hz=10

# Track info
GET http://localhost:8000/api/session/2024/5/R/track

# Complete replay data
GET http://localhost:8000/api/session/2024/5/R/replay?hz=10&drivers=VER,HAM

# Interactive docs
http://localhost:8000/docs
```

## Session Types

| Code  | Description       |
| ----- | ----------------- |
| `FP1` | Free Practice 1   |
| `FP2` | Free Practice 2   |
| `FP3` | Free Practice 3   |
| `Q`   | Qualifying        |
| `S`   | Sprint Race       |
| `SQ`  | Sprint Qualifying |
| `R`   | Race              |

## Configuration (.env)

```env
# Cache location
FASTF1_CACHE=./cache

# Telemetry frequency (5-20 Hz)
TELEMETRY_FREQUENCY_HZ=10

# Turn detection threshold (10-25 degrees)
TURN_DETECTION_THRESHOLD=15

# Default playback speed
DEFAULT_SPEED_MULTIPLIER=1.0
```

## Troubleshooting

### Issue: Session won't load

**Solution**: Check GP number/name and session type are correct

### Issue: Missing drivers

**Solution**: Normal if drivers retired from session

### Issue: Slow performance

**Solution**: Reduce Hz (`--hz 5`) or limit drivers (`--drivers VER HAM`)

### Issue: Arcade window won't open

**Solution**: Update arcade (`pip install --upgrade arcade`)

## Project Structure

```
F1PitStop/
├── app.py              # Main entry point
├── requirements.txt    # Dependencies
├── .env               # Configuration
├── data/              # Data loading
├── visual/            # Arcade replay
├── api/               # FastAPI server
├── utils/             # Utilities
└── tests/             # Unit tests
```

## Key Functions Reference

### Data Loading

```python
from data.loader import load_session
session = load_session(2024, 5, "R")
```

### Telemetry Processing

```python
from data.telemetry import extract_driver_telemetry, build_common_timebase
telemetry = extract_driver_telemetry(session, "VER")
timeline = build_common_timebase({"VER": telemetry}, hz=10)
```

### Turn Detection

```python
from data.telemetry import compute_turns, get_track_coordinates
coords = get_track_coordinates(session)
turns = compute_turns(coords)
```

## Development Workflow

1. Make changes to code
2. Run tests: `pytest tests/ -v`
3. Test manually: `python app.py --year 2024 --gp 5 --session R`
4. Commit changes
5. CI runs automatically on push

## Support

- Check README.md for detailed documentation
- Review tests/ for usage examples
- API docs at http://localhost:8000/docs
- Error logs in console output
