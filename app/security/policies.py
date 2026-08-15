from typing import Dict, Any, Optional
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.security")

class SecurityPolicy:
    """Evaluates whether a tool execution requires user confirmation based on risk levels."""

    def __init__(self, default_permission_level: int = 1, require_confirmation_for_risky: bool = True):
        self.default_permission_level = default_permission_level
        self.require_confirmation_for_risky = require_confirmation_for_risky

    def requires_confirmation(self, tool_name: str, risk_level: int) -> bool:
        """
        Risk Levels:
        - 0: Safe (Read time, open browser, screenshot) -> No confirmation
        - 1: Low (Create folder, write text) -> Auto-approved by default
        - 2: Moderate (Close applications) -> Confirmation requested if configured
        - 3: High/Destructive (Delete files, modify system) -> ALWAYS requires explicit confirmation
        """
        if risk_level >= 3:
            return True
        if risk_level >= 2 and self.require_confirmation_for_risky:
            return True
        return False
