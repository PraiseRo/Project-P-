from enum import Enum
from typing import Callable, Dict, List, Any
import inspect

class AssistantState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"

class EventBus:
    """Decoupled asynchronous/synchronous publish-subscribe event bus for the assistant."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Any], None]):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def publish(self, event_name: str, data: Any = None):
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    import logging
                    logging.getLogger("assistant.events").error(
                        f"Error in event callback for '{event_name}': {e}", exc_info=True
                    )

# Global event bus singleton
event_bus = EventBus()
