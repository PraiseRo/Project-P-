import os
import subprocess
import psutil
from typing import Dict, Any, List
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tools.apps")

COMMON_APP_MAPPINGS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code"
}

@tool_registry.register(
    name="open_application",
    description="Launch an installed Windows application or executable.",
    parameters={
        "application_name": {
            "type": "string",
            "description": "Name or executable of the application to open (e.g. 'notepad', 'chrome', 'calculator')."
        }
    },
    required=["application_name"],
    risk_level=0
)
def open_application(application_name: str) -> Dict[str, Any]:
    app_lower = application_name.lower().strip()
    target_cmd = COMMON_APP_MAPPINGS.get(app_lower, application_name)

    try:
        # Launch using Windows start/shell command
        os.startfile(target_cmd)
        logger.info(f"Opened application: {target_cmd}")
        return {"status": "success", "message": f"Successfully opened {application_name}."}
    except Exception as e:
        # Fallback to subprocess
        try:
            subprocess.Popen(target_cmd, shell=True)
            logger.info(f"Launched application via subprocess: {target_cmd}")
            return {"status": "success", "message": f"Launched {application_name}."}
        except Exception as err:
            logger.error(f"Failed to open application '{application_name}': {err}")
            return {"status": "error", "message": f"Could not open {application_name}: {str(err)}"}


@tool_registry.register(
    name="close_application",
    description="Close or terminate a running process by application name.",
    parameters={
        "application_name": {
            "type": "string",
            "description": "Name of the process/application to close (e.g. 'notepad', 'chrome')."
        }
    },
    required=["application_name"],
    risk_level=2
)
def close_application(application_name: str) -> Dict[str, Any]:
    target = application_name.lower().replace(".exe", "")
    closed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower().replace(".exe", "")
            if target == proc_name or target in proc_name:
                proc.terminate()
                closed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if closed_count > 0:
        return {"status": "success", "message": f"Closed {closed_count} instance(s) of {application_name}."}
    return {"status": "warning", "message": f"No running instances found for {application_name}."}
