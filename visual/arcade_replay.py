"""
Arcade-based replay visualization for Formula 1 sessions.

This module provides an interactive track visualization window using the Arcade
library, displaying driver positions, telemetry, and replay controls.
"""

import math
from typing import Dict, List, Optional, Tuple

import arcade
import arcade.shape_list as shape_list
import numpy as np
import pandas as pd

from utils.colors import (
    get_driver_color,
    get_tyre_color,
    get_speed_heatmap_color,
)

# F1-inspired palette
F1_BLACK = (6, 7, 9)
F1_DARK = (15, 18, 24)
F1_PANEL = (18, 21, 28, 220)
F1_HUD = (10, 12, 16, 220)
F1_RED = (220, 0, 0)
TRACK_COLOR = (120, 120, 125)
TURN_COLOR = arcade.color.YELLOW
TEXT_MAIN = arcade.color.LIGHT_GRAY
TEXT_ACCENT = arcade.color.WHITE


class F1ReplayWindow(arcade.Window):
    """
    Interactive F1 replay visualization window.

    This window displays the race track, driver positions (as colored dots),
    telemetry information, and provides interactive controls for replay navigation.

    Features:
    - Track visualization with turn markers and sector boundaries
    - Real-time driver position updates
    - Play/pause, step forward/backward, speed control
    - Telemetry overlays (speed, tyre compound, gear)
    - Legend and HUD with session information
    - Tooltips explaining F1 terminology for new viewers

    Keyboard Controls:
    - Space: Play/Pause
    - Right Arrow: Step forward 1 second
    - Left Arrow: Step backward 1 second
    - Up Arrow: Increase speed multiplier
    - Down Arrow: Decrease speed multiplier
    - 1-9: Focus on specific driver
    - H: Toggle help overlay
    - T: Toggle telemetry overlay
    - M: Toggle map/replay mode
    """

    def __init__(
        self,
        width: int = 1400,
        height: int = 900,
        track_coords: np.ndarray = None,
        drivers: Dict[str, pd.DataFrame] = None,
        timeline: np.ndarray = None,
        turns: List[Dict] = None,
        session_info: Dict = None,
        top_speeds: Dict = None,
    ):
        """
        Initialize the F1 replay window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            track_coords: Numpy array of shape (N, 2) with track X, Y coordinates.
            drivers: Dict mapping driver codes to telemetry DataFrames (interpolated).
            timeline: Common timebase array in seconds.
            turns: List of detected turns with position and metadata.
            session_info: Dictionary with session metadata.
            top_speeds: Dictionary with top speed information.
        """
        super().__init__(width, height, "F1 Pit Stop - Interactive Replay")

        # Set background color
        arcade.set_background_color(F1_BLACK)

        # Track and session data
        self.track_coords = track_coords if track_coords is not None else np.array([])
        self.drivers = drivers if drivers is not None else {}
        self.timeline = timeline if timeline is not None else np.array([])
        self.turns = turns if turns is not None else []
        self.session_info = session_info if session_info is not None else {}
        self.top_speeds = top_speeds if top_speeds is not None else {}

        # Replay state
        self.current_time_index = 0
        self.is_playing = False
        self.speed_multiplier = 1.0
        self.accumulated_time = 0.0

        # View state
        self.camera_x = 0
        self.camera_y = 0
        self.zoom_level = 1.0
        self.show_telemetry = True
        self.show_help = False
        self.focused_driver = None

        # Track rendering
        self.track_center_x = 0
        self.track_center_y = 0
        self.track_scale = 1.0

        # UI elements
        self.driver_list = sorted(self.drivers.keys())

        # Calculate track bounds and centering
        self._calculate_track_bounds()

    def _calculate_track_bounds(self):
        """Calculate track bounds and scaling for proper display."""
        if len(self.track_coords) == 0:
            return

        # Find min/max coordinates
        min_x = self.track_coords[:, 0].min()
        max_x = self.track_coords[:, 0].max()
        min_y = self.track_coords[:, 1].min()
        max_y = self.track_coords[:, 1].max()

        # Calculate dimensions
        track_width = max_x - min_x
        track_height = max_y - min_y

        # Calculate scale to fit in window (with padding)
        padding = 100  # pixels
        scale_x = (self.width - 2 * padding) / track_width if track_width > 0 else 1
        scale_y = (
            (self.height - 2 * padding - 150) / track_height if track_height > 0 else 1
        )  # 150 for HUD

        # Use smaller scale to maintain aspect ratio
        self.track_scale = min(scale_x, scale_y)

        # Calculate center offset
        track_center_x_world = (min_x + max_x) / 2
        track_center_y_world = (min_y + max_y) / 2

        self.track_center_x = self.width / 2 - track_center_x_world * self.track_scale
        self.track_center_y = (
            (self.height - 150) / 2 - track_center_y_world * self.track_scale + 75
        )

    def _world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert world coordinates (meters) to screen coordinates (pixels).

        Args:
            x: World X coordinate in meters.
            y: World Y coordinate in meters.

        Returns:
            Tuple of (screen_x, screen_y) in pixels.
        """
        screen_x = (
            x * self.track_scale * self.zoom_level + self.track_center_x + self.camera_x
        )
        screen_y = (
            y * self.track_scale * self.zoom_level + self.track_center_y + self.camera_y
        )
        return screen_x, screen_y

    def on_draw(self):
        """Render the track, drivers, and UI elements."""
        self.clear()

        # Draw track
        self._draw_track()

        # Draw turns
        self._draw_turns()

        # Draw drivers
        self._draw_drivers()

        # Draw HUD
        self._draw_hud()

        # Draw legend
        self._draw_legend()

        # Draw controls
        self._draw_controls()

        # Draw help overlay if enabled
        if self.show_help:
            self._draw_help_overlay()

    def _draw_track(self):
        """Draw the race track as a line."""
        if len(self.track_coords) < 2:
            return

        # Convert all track points to screen coordinates
        screen_points = []
        for i in range(len(self.track_coords)):
            sx, sy = self._world_to_screen(
                self.track_coords[i, 0], self.track_coords[i, 1]
            )
            screen_points.append((sx, sy))

        # Draw track as lines
        for i in range(len(screen_points) - 1):
            arcade.draw.draw_line(
                screen_points[i][0],
                screen_points[i][1],
                screen_points[i + 1][0],
                screen_points[i + 1][1],
                TRACK_COLOR,
                3,
            )

        # Connect last point to first (close the loop)
        if len(screen_points) > 2:
            arcade.draw.draw_line(
                screen_points[-1][0],
                screen_points[-1][1],
                screen_points[0][0],
                screen_points[0][1],
                TRACK_COLOR,
                3,
            )

        # Start/finish marker
        if len(screen_points) > 1:
            s0 = screen_points[0]
            s1 = screen_points[1]
            arcade.draw.draw_line(
                s0[0],
                s0[1],
                s1[0],
                s1[1],
                F1_RED,
                4,
            )

    def _draw_turns(self):
        """Draw turn markers and numbers on the track."""
        for turn in self.turns:
            sx, sy = self._world_to_screen(turn["x"], turn["y"])

            # Draw turn marker circle
            arcade.draw.draw_circle_filled(sx, sy, 5, TURN_COLOR)

            # Draw turn number
            turn_num = turn["name"].split()[-1]  # Extract number from "Turn X"
            arcade.draw_text(
                turn_num, sx + 8, sy - 4, arcade.color.WHITE, 12, bold=True
            )

    def _draw_drivers(self):
        """Draw driver positions as colored dots with tyre indicators."""
        if self.current_time_index >= len(self.timeline):
            return

        for driver_code in self.driver_list:
            telemetry = self.drivers.get(driver_code)
            if telemetry is None or telemetry.empty:
                continue

            if self.current_time_index >= len(telemetry):
                continue

            row = telemetry.iloc[self.current_time_index]

            # Skip if no position data
            if pd.isna(row.get("X")) or pd.isna(row.get("Y")):
                continue

            # Get screen position
            sx, sy = self._world_to_screen(row["X"], row["Y"])

            # Get driver color
            color = get_driver_color(driver_code)

            # Draw driver dot
            dot_radius = 8 if driver_code == self.focused_driver else 6
            arcade.draw.draw_circle_filled(sx, sy, dot_radius, color)

            # Draw border for focused driver
            if driver_code == self.focused_driver:
                arcade.draw.draw_circle_outline(
                    sx, sy, dot_radius + 2, arcade.color.WHITE, 2
                )

            # Draw tyre indicator
            if "Compound" in row and pd.notna(row["Compound"]):
                tyre_color = get_tyre_color(row["Compound"])
                # Small square below the dot
                # In Arcade 3.x use lbwh (left, bottom, width, height) for rectangles
                arcade.draw.draw_lbwh_rectangle_filled(sx - 4, sy - 14, 8, 4, tyre_color)

            # Draw telemetry overlay if enabled
            if self.show_telemetry and (
                driver_code == self.focused_driver or self.focused_driver is None
            ):
                self._draw_driver_telemetry(driver_code, sx, sy, row)

    def _draw_driver_telemetry(
        self,
        driver_code: str,
        screen_x: float,
        screen_y: float,
        telemetry_row: pd.Series,
    ):
        """
        Draw telemetry information near a driver.

        Args:
            driver_code: Driver code.
            screen_x: Screen X position.
            screen_y: Screen Y position.
            telemetry_row: Telemetry data row.
        """
        # Build telemetry text
        info_lines = [driver_code]

        if "Speed" in telemetry_row and pd.notna(telemetry_row["Speed"]):
            info_lines.append(f"{telemetry_row['Speed']:.0f} km/h")

        if "nGear" in telemetry_row and pd.notna(telemetry_row["nGear"]):
            info_lines.append(f"Gear {int(telemetry_row['nGear'])}")

        # Draw background box
        text_y = screen_y + 15
        for line in info_lines:
            arcade.draw_text(
                line, screen_x + 10, text_y, arcade.color.WHITE, 10, bold=True
            )
            text_y += 12

    def _draw_hud(self):
        """Draw the heads-up display with session info and controls."""
        # HUD background
        arcade.draw.draw_lrbt_rectangle_filled(
            0, self.width, self.height - 80, self.height, F1_HUD
        )
        # Accent strip
        arcade.draw.draw_lrbt_rectangle_filled(
            0, self.width, self.height - 78, self.height, (F1_RED[0], F1_RED[1], F1_RED[2], 220)
        )

        # Session name
        session_name = self.session_info.get("event_name", "F1 Session")
        session_type = self.session_info.get("session_name", "Race")
        arcade.draw_text(
            f"{session_name} - {session_type}",
            10,
            self.height - 25,
            arcade.color.WHITE,
            16,
            bold=True,
        )

        # Current time
        if len(self.timeline) > 0 and self.current_time_index < len(self.timeline):
            current_time = self.timeline[self.current_time_index]
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            arcade.draw_text(
                f"Time: {minutes:02d}:{seconds:02d}",
                10,
                self.height - 50,
                arcade.color.WHITE,
                14,
            )

        # Play/pause status
        status = "▶ PLAYING" if self.is_playing else "⏸ PAUSED"
        arcade.draw_text(
            status,
            200,
            self.height - 50,
            arcade.color.GREEN if self.is_playing else arcade.color.YELLOW,
            14,
            bold=True,
        )

        # Speed multiplier
        arcade.draw_text(
            f"Speed: {self.speed_multiplier:.2f}x",
            350,
            self.height - 50,
            arcade.color.WHITE,
            14,
        )

        # Top speed info
        if self.top_speeds.get("overall_max_driver"):
            arcade.draw_text(
                f"Top Speed: {self.top_speeds['overall_max']:.1f} km/h ({self.top_speeds['overall_max_driver']})",
                500,
                self.height - 50,
                arcade.color.ORANGE,
                14,
            )

        # Turn count
        arcade.draw_text(
            f"Turns: {len(self.turns)}",
            self.width - 120,
            self.height - 50,
            arcade.color.WHITE,
            14,
        )

    def _draw_legend(self):
        """Draw driver legend with colors and tyre info."""
        legend_x = self.width - 180
        legend_y = self.height - 120

        # Legend background
        legend_height = len(self.driver_list) * 25 + 40
        arcade.draw.draw_lrbt_rectangle_filled(
            legend_x, legend_x + 160, legend_y - legend_height, legend_y, (0, 0, 0, 200)
        )

        # Title
        arcade.draw_text(
            "Drivers", legend_x, legend_y, arcade.color.WHITE, 12, bold=True
        )

        legend_y -= 25

        # Draw each driver
        for driver_code in self.driver_list:
            color = get_driver_color(driver_code)

            # Draw color indicator
            arcade.draw.draw_circle_filled(legend_x + 8, legend_y, 5, color)

            # Draw driver code
            arcade.draw_text(
                driver_code, legend_x + 20, legend_y - 5, arcade.color.WHITE, 11
            )

            # Draw current tyre if available
            if driver_code in self.drivers and self.current_time_index < len(
                self.drivers[driver_code]
            ):
                telemetry = self.drivers[driver_code]
                row = telemetry.iloc[self.current_time_index]
                if "Compound" in row and pd.notna(row["Compound"]):
                    tyre_color = get_tyre_color(row["Compound"])
                    arcade.draw.draw_lrbt_rectangle_filled(
                        legend_x + 80,
                        legend_x + 120,
                        legend_y - 4,
                        legend_y + 4,
                        tyre_color,
                    )
                    # Compound initial
                    compound_initial = row["Compound"][0] if row["Compound"] else "?"
                    arcade.draw_text(
                        compound_initial,
                        legend_x + 85,
                        legend_y - 5,
                        arcade.color.WHITE,
                        10,
                    )

            legend_y -= 20

    def _draw_controls(self):
        """Draw control instructions at the bottom."""
        controls_y = 30

        arcade.draw_text(
            "Controls: SPACE=Play/Pause | ←/→=Step | ↑/↓=Speed | H=Help | T=Telemetry",
            self.width / 2,
            controls_y,
            arcade.color.LIGHT_GRAY,
            11,
            anchor_x="center",
        )

    def _draw_help_overlay(self):
        """Draw help overlay explaining F1 terminology for new viewers."""
        # Semi-transparent background
        center_x = self.width / 2
        center_y = self.height / 2
        arcade.draw.draw_lrbt_rectangle_filled(
            center_x - 300,
            center_x + 300,
            center_y - 250,
            center_y + 250,
            (0, 0, 0, 230),
        )

        # Border
        arcade.draw.draw_lrbt_rectangle_outline(
            center_x - 300,
            center_x + 300,
            center_y - 250,
            center_y + 250,
            arcade.color.WHITE,
            3,
        )

        # Title
        arcade.draw_text(
            "F1 Viewer's Guide",
            self.width / 2,
            self.height / 2 + 220,
            arcade.color.WHITE,
            20,
            anchor_x="center",
            bold=True,
        )

        # Help text
        help_text = [
            "",
            "TYRE COMPOUNDS:",
            "• Soft (Red): Fastest but wears out quickly",
            "• Medium (Yellow): Balanced performance",
            "• Hard (White): Slowest but lasts longest",
            "• Intermediate (Green): For light rain",
            "• Wet (Blue): For heavy rain",
            "",
            "TRACK ELEMENTS:",
            "• Yellow dots: Turn markers (numbered)",
            "• Gray line: Race track layout",
            "• Colored dots: Driver positions",
            "",
            "TELEMETRY:",
            "• Speed: Current velocity in km/h",
            "• Gear: Current transmission gear (1-8)",
            "• Lap: Current lap number",
            "",
            "Press H to close this help",
        ]

        y = self.height / 2 + 180
        for line in help_text:
            arcade.draw_text(
                line,
                self.width / 2 - 270,
                y,
                (
                    arcade.color.WHITE
                    if line and line[0] not in ["•", "P"]
                    else arcade.color.LIGHT_GRAY
                ),
                12,
                bold=line and line.isupper(),
            )
            y -= 20

    def on_update(self, delta_time: float):
        """
        Update replay state based on play/pause and speed multiplier.

        Args:
            delta_time: Time elapsed since last update in seconds.

        Notes:
            Frame rate independent movement using delta_time and speed_multiplier.
        """
        if not self.is_playing or len(self.timeline) == 0:
            return

        # Accumulate time with speed multiplier
        self.accumulated_time += delta_time * self.speed_multiplier

        # Determine how many time steps to advance
        # Each step in timeline represents a fixed time interval
        if len(self.timeline) > 1:
            time_step = self.timeline[1] - self.timeline[0]
            steps_to_advance = int(self.accumulated_time / time_step)

            if steps_to_advance > 0:
                self.current_time_index += steps_to_advance
                self.accumulated_time -= steps_to_advance * time_step

                # Wrap or stop at end
                if self.current_time_index >= len(self.timeline):
                    self.current_time_index = len(self.timeline) - 1
                    self.is_playing = False
                    print("Replay finished")

    def on_key_press(self, key, modifiers):
        """
        Handle keyboard input for controls.

        Args:
            key: Key code that was pressed.
            modifiers: Modifier keys held (Shift, Ctrl, etc.).
        """
        # Play/Pause
        if key == arcade.key.SPACE:
            self.play() if not self.is_playing else self.pause()

        # Step forward
        elif key == arcade.key.RIGHT:
            self.step_forward(1.0)

        # Step backward
        elif key == arcade.key.LEFT:
            self.step_backward(1.0)

        # Increase speed
        elif key == arcade.key.UP:
            self.speed_multiplier = min(self.speed_multiplier * 2, 8.0)
            print(f"Speed: {self.speed_multiplier}x")

        # Decrease speed
        elif key == arcade.key.DOWN:
            self.speed_multiplier = max(self.speed_multiplier / 2, 0.25)
            print(f"Speed: {self.speed_multiplier}x")

        # Toggle help
        elif key == arcade.key.H:
            self.show_help = not self.show_help

        # Toggle telemetry
        elif key == arcade.key.T:
            self.show_telemetry = not self.show_telemetry
            print(f"Telemetry: {'ON' if self.show_telemetry else 'OFF'}")

        # Number keys for driver focus
        elif arcade.key.KEY_1 <= key <= arcade.key.KEY_9:
            driver_index = key - arcade.key.KEY_1
            if driver_index < len(self.driver_list):
                self.focused_driver = self.driver_list[driver_index]
                print(f"Focused on: {self.focused_driver}")
            else:
                self.focused_driver = None

        # Reset focus
        elif key == arcade.key.KEY_0:
            self.focused_driver = None
            print("Focus reset")

    def play(self):
        """Start replay playback."""
        self.is_playing = True
        print("▶ Playing")

    def pause(self):
        """Pause replay playback."""
        self.is_playing = False
        self.accumulated_time = 0.0
        print("⏸ Paused")

    def step_forward(self, seconds: float):
        """
        Step forward by a specified number of seconds.

        Args:
            seconds: Number of seconds to advance.
        """
        if len(self.timeline) < 2:
            return

        time_step = self.timeline[1] - self.timeline[0]
        steps = int(seconds / time_step)

        self.current_time_index = min(
            self.current_time_index + steps, len(self.timeline) - 1
        )
        print(f"Stepped forward to {self.timeline[self.current_time_index]:.1f}s")

    def step_backward(self, seconds: float):
        """
        Step backward by a specified number of seconds.

        Args:
            seconds: Number of seconds to go back.
        """
        if len(self.timeline) < 2:
            return

        time_step = self.timeline[1] - self.timeline[0]
        steps = int(seconds / time_step)

        self.current_time_index = max(self.current_time_index - steps, 0)
        print(f"Stepped backward to {self.timeline[self.current_time_index]:.1f}s")

    def jump_to(self, time_sec: float):
        """
        Jump to a specific time in the replay.

        Args:
            time_sec: Target time in seconds.
        """
        if len(self.timeline) == 0:
            return

        # Find nearest index
        idx = np.searchsorted(self.timeline, time_sec)
        self.current_time_index = min(idx, len(self.timeline) - 1)
        print(f"Jumped to {self.timeline[self.current_time_index]:.1f}s")
