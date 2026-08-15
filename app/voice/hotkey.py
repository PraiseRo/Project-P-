from typing import Callable, Optional
from pynput import keyboard
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.hotkey")

class PushToTalkListener:
    """Monitors global key press and release to manage push-to-talk recording states."""

    def __init__(
        self,
        on_press_callback: Callable[[], None],
        on_release_callback: Callable[[], None],
        on_emergency_stop: Optional[Callable[[], None]] = None
    ):
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback
        self.on_emergency_stop = on_emergency_stop
        self._listener: Optional[keyboard.Listener] = None
        self._is_pressed = False
        self._ctrl_down = False
        self._alt_down = False

    def _on_press(self, key):
        try:
            if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                self._ctrl_down = True
            elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                self._alt_down = True
            
            # Check for Emergency Stop: Ctrl + Alt + Esc or Esc alone when active
            if key == keyboard.Key.esc and (self._ctrl_down or self._alt_down):
                if self.on_emergency_stop:
                    logger.warning("Emergency Stop Hotkey Triggered!")
                    self.on_emergency_stop()
                return

            # Check for Push-to-Talk (Default: Ctrl + Space)
            if key == keyboard.Key.space and self._ctrl_down:
                if not self._is_pressed:
                    self._is_pressed = True
                    logger.info("Push-to-Talk activated.")
                    self.on_press_callback()
        except Exception as e:
            logger.error(f"Error handling key press: {e}")

    def _on_release(self, key):
        try:
            if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                self._ctrl_down = False
            elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                self._alt_down = False

            if self._is_pressed:
                if key == keyboard.Key.space or not self._ctrl_down:
                    self._is_pressed = False
                    logger.info("Push-to-Talk released.")
                    self.on_release_callback()
        except Exception as e:
            logger.error(f"Error handling key release: {e}")

    def start(self):
        """Starts background hotkey listening thread."""
        if self._listener is None:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()
            logger.info("Global hotkey listener started.")

    def stop(self):
        """Stops background hotkey listening thread."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            logger.info("Global hotkey listener stopped.")
