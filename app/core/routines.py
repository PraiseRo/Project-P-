import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.routines")

ROUTINES_FILE_PATH = Path(__file__).parent.parent / "config" / "routines.json"

class RoutineManager:
    """Manages loading, matching, and chained execution of custom multi-step offline routines."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or ROUTINES_FILE_PATH
        self.routines: Dict[str, Dict[str, Any]] = {}
        self.load_routines()

    def load_routines(self):
        """Loads routines from JSON configuration file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.routines = json.load(f)
                logger.info(f"Loaded {len(self.routines)} custom routines from {self.config_path.name}")
            except Exception as e:
                logger.error(f"Failed to load routines from {self.config_path}: {e}")
                self.routines = {}
        else:
            self.routines = {}

    def save_routines(self):
        """Persists current routines dictionary to JSON."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.routines, f, indent=2)
            logger.info("Routines saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save routines: {e}")

    def match_routine(self, query: str) -> Optional[Dict[str, Any]]:
        """Matches a user voice query against registered routine trigger phrases."""
        clean = query.lower().strip()

        # Direct match
        for name, routine in self.routines.items():
            trigger = name.lower()
            if trigger in clean or clean in trigger:
                return routine

        # Fuzzy match for common synonyms
        if "workspace" in clean or "work space" in clean:
            return self.routines.get("setup my workspace")
        if "study" in clean or "relax" in clean:
            return self.routines.get("study mode")

        return None

    async def execute_routine(self, routine: Dict[str, Any]) -> str:
        """Executes all actions in a routine sequentially."""
        actions = routine.get("actions", [])
        spoken = routine.get("spoken_response", "Routine completed.")

        logger.info(f"Executing routine with {len(actions)} actions...")
        for action in actions:
            tool_name = action.get("tool")
            args = action.get("args", {})
            try:
                logger.info(f"Routine step: executing {tool_name} with {args}")
                await tool_registry.execute(tool_name, args)
                # Small micro-delay for smooth OS window launches
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error executing routine step '{tool_name}': {e}")

        return spoken

# Global routine manager singleton
routine_manager = RoutineManager()
