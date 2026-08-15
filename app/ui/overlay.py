import tkinter as tk
import math
import time
from typing import Callable, Optional
from app.core.events import AssistantState, event_bus
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.ui.orb")

class AssistantOverlay(tk.Tk):
    """
    Project P: Sleek, futuristic circular floating orb widget with dynamic animated soundwaves
    anchored at the bottom-right corner of the Windows screen.
    """

    def __init__(self, on_text_submit: Optional[Callable[[str], None]] = None, on_click_toggle: Optional[Callable[[], None]] = None):
        super().__init__()
        self.on_text_submit = on_text_submit
        self.on_click_toggle = on_click_toggle

        # Window settings: borderless, always on top, transparent background
        self.title("Project P")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)
        self.config(bg="#050811")
        self.wm_attributes("-transparentcolor", "#050811")

        self.widget_width = 340
        self.widget_height = 240
        self.orb_size = 90

        # Position at bottom-right corner of the screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = screen_w - self.widget_width - 30
        pos_y = screen_h - self.widget_height - 60
        self.geometry(f"{self.widget_width}x{self.widget_height}+{pos_x}+{pos_y}")

        # Dragging support
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Canvas for drawing glowing orb and animated sine soundwaves
        self.canvas = tk.Canvas(
            self,
            width=self.widget_width,
            height=self.widget_height,
            bg="#050811",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # State tracking
        self.current_state = AssistantState.IDLE
        self.animation_phase = 0.0
        self.transcript_text = "Project P is ready (Ctrl+Space)"
        self.transcript_speaker = "Project P"
        self.bubble_alpha = 1.0

        # Event Bus subscriptions
        event_bus.subscribe("state_change", self._on_state_change)
        event_bus.subscribe("user_message", self._on_user_message)
        event_bus.subscribe("assistant_message", self._on_assistant_message)

        # Start animation loop (60 FPS)
        self._animate()

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def _on_state_change(self, state: AssistantState):
        self.current_state = state

    def _on_user_message(self, text: str):
        self.transcript_speaker = "You"
        self.transcript_text = text

    def _on_assistant_message(self, text: str):
        self.transcript_speaker = "Project P"
        self.transcript_text = text

    def _animate(self):
        self.animation_phase += 0.12
        self.canvas.delete("all")

        # Orb Center Coordinates
        cx = self.widget_width - 55
        cy = self.widget_height - 55
        r = 34

        # 1. Draw Speech / Status Bubble (above the orb)
        if self.transcript_text:
            text_str = self.transcript_text
            if len(text_str) > 75:
                text_str = text_str[:72] + "..."

            # Speech bubble background pill
            bubble_w = min(270, max(140, len(text_str) * 7 + 30))
            bubble_h = 42
            bx1 = cx - bubble_w + 20
            by1 = cy - 65
            bx2 = cx + 20
            by2 = by1 + bubble_h

            # Bubble background
            self.canvas.create_rectangle(
                bx1, by1, bx2, by2,
                fill="#121829",
                outline="#2A3B5C",
                width=1.5
            )

            # Bubble Header / Speaker tag
            header_color = "#00F2FE" if self.transcript_speaker == "Project P" else "#4FACFE"
            if self.current_state == AssistantState.LISTENING:
                header_color = "#FF0844"
                status_text = "● LISTENING"
            elif self.current_state == AssistantState.THINKING:
                header_color = "#FFAA00"
                status_text = "● THINKING"
            elif self.current_state == AssistantState.EXECUTING:
                header_color = "#7F00FF"
                status_text = "● EXECUTING"
            else:
                status_text = self.transcript_speaker

            self.canvas.create_text(
                bx1 + 10, by1 + 10,
                text=status_text,
                fill=header_color,
                font=("Segoe UI", 8, "bold"),
                anchor="w"
            )

            # Transcript message body
            self.canvas.create_text(
                bx1 + 10, by1 + 26,
                text=text_str,
                fill="#F0F4F8",
                font=("Segoe UI", 9),
                anchor="w"
            )

        # 2. Draw Glowing Aura Rings
        if self.current_state == AssistantState.LISTENING:
            glow_color = "#FF0844"
            wave_color_1 = "#FF4E50"
            wave_color_2 = "#F9D423"
            num_waves = 4
            amplitude = 12
        elif self.current_state == AssistantState.THINKING:
            glow_color = "#FFAA00"
            wave_color_1 = "#FF8008"
            wave_color_2 = "#FFC837"
            num_waves = 3
            amplitude = 8
        elif self.current_state == AssistantState.EXECUTING:
            glow_color = "#7F00FF"
            wave_color_1 = "#E100FF"
            wave_color_2 = "#7F00FF"
            num_waves = 3
            amplitude = 9
        elif self.current_state == AssistantState.SPEAKING:
            glow_color = "#00F2FE"
            wave_color_1 = "#4FACFE"
            wave_color_2 = "#00F2FE"
            num_waves = 4
            amplitude = 14
        else:
            # IDLE - Gentle breathing cyan/blue glow
            glow_color = "#1E3C72"
            wave_color_1 = "#2A5298"
            wave_color_2 = "#4FACFE"
            num_waves = 2
            amplitude = 3

        # Pulse radius
        pulse = math.sin(self.animation_phase * 0.8) * 3
        current_r = r + pulse

        # Outer soft glow ring
        self.canvas.create_oval(
            cx - current_r - 8, cy - current_r - 8,
            cx + current_r + 8, cy + current_r + 8,
            fill="#0F172A",
            outline=glow_color,
            width=2
        )

        # 3. Draw Dynamic Animated Sine Soundwaves inside the Orb
        points = []
        for i in range(-28, 29, 2):
            x = cx + i
            # Calculate bell curve attenuation near edges of the circle
            factor = math.cos((i / 28.0) * (math.pi / 2.0))
            y_offset = math.sin((i * 0.25) + self.animation_phase * 1.5) * amplitude * factor
            points.extend([x, cy + y_offset])

        if len(points) >= 4:
            self.canvas.create_line(points, fill=wave_color_1, width=3, smooth=True)

        # Second cross-harmonic wave
        points2 = []
        for i in range(-25, 26, 2):
            x = cx + i
            factor = math.cos((i / 25.0) * (math.pi / 2.0))
            y_offset = math.cos((i * 0.3) - self.animation_phase * 1.8) * (amplitude * 0.7) * factor
            points2.extend([x, cy + y_offset])

        if len(points2) >= 4:
            self.canvas.create_line(points2, fill=wave_color_2, width=2, smooth=True)

        # Center core energy dot (The "P" Core)
        core_glow = "#FFFFFF" if self.current_state != AssistantState.IDLE else "#4FACFE"
        self.canvas.create_oval(
            cx - 3, cy - 3, cx + 3, cy + 3,
            fill=core_glow,
            outline=""
        )

        # 4. Schedule next frame (60 FPS = ~16ms)
        self.after(16, self._animate)
