import platform
import psutil
import pyautogui
import tempfile
from typing import Dict, Any
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tools.system")

@tool_registry.register(
    name="get_system_info",
    description="Retrieve PC system metrics including OS version, CPU usage, and Memory load.",
    parameters={},
    risk_level=0
)
def get_system_info() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    return {
        "status": "success",
        "os": f"{platform.system()} {platform.release()}",
        "cpu_usage_percent": cpu_percent,
        "memory_used_percent": memory.percent,
        "memory_available_gb": round(memory.available / (1024 ** 3), 2)
    }

@tool_registry.register(
    name="take_screenshot",
    description="Take a screenshot of the current active screen.",
    parameters={},
    risk_level=0
)
def take_screenshot() -> Dict[str, Any]:
    try:
        screenshot = pyautogui.screenshot()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
        screenshot.save(temp_path)
        logger.info(f"Screenshot saved to: {temp_path}")
        return {
            "status": "success",
            "message": "Screenshot captured successfully.",
            "file_path": temp_path
        }
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return {"status": "error", "message": f"Screenshot failed: {str(e)}"}
