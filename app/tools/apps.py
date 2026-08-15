import os
import subprocess
import psutil
import difflib
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tools.apps")

COMMON_APP_MAPPINGS = {
    # Accessories & Creative
    "paint": "mspaint.exe",
    "paint app": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "ms paint": "mspaint.exe",
    "drawing": "mspaint.exe",
    "draw": "mspaint.exe",
    "snipping tool": "snippingtool.exe",
    "snip": "snippingtool.exe",
    "screenshot tool": "snippingtool.exe",
    "notepad": "notepad.exe",
    "text editor": "notepad.exe",
    "wordpad": "write.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",

    # Browsers
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "google": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",

    # Productivity & Communication
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "code": "code",
    "discord": "discord.exe",
    "spotify": "spotify.exe",
    "music": "spotify.exe",
    "telegram": "telegram.exe",
    "whatsapp": "whatsapp.exe",
    "slack": "slack.exe",
    "zoom": "zoom.exe",

    # Microsoft Office
    "word": "winword.exe",
    "ms word": "winword.exe",
    "excel": "excel.exe",
    "ms excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",

    # System & Utilities
    "settings": "ms-settings:",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "files": "explorer.exe",
    "my computer": "explorer.exe",
    "this pc": "explorer.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "camera": "microsoft.windows.camera:",
}

def _discover_windows_app(app_name: str) -> Optional[str]:
    """Dynamically locates executables and shortcuts in Start Menu and Program Files."""
    clean = app_name.lower().strip().replace(" app", "").replace(" application", "")
    
    # 1. Check common direct mappings
    if clean in COMMON_APP_MAPPINGS:
        return COMMON_APP_MAPPINGS[clean]

    # 2. Fuzzy match against known aliases
    matches = difflib.get_close_matches(clean, COMMON_APP_MAPPINGS.keys(), n=1, cutoff=0.6)
    if matches:
        logger.info(f"Fuzzy matched '{app_name}' to '{matches[0]}'")
        return COMMON_APP_MAPPINGS[matches[0]]

    # 3. Check Windows Start Menu shortcuts (.lnk files)
    start_menu_paths = [
        Path(os.environ.get("ProgramData", "C:/ProgramData")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]

    for base_dir in start_menu_paths:
        if base_dir.exists():
            for link in base_dir.rglob("*.lnk"):
                if clean in link.stem.lower():
                    logger.info(f"Discovered installed app shortcut: {link}")
                    return str(link)

    return None

@tool_registry.register(
    name="open_application",
    description="Launch an installed Windows application or executable (e.g. 'paint', 'notepad', 'chrome', 'calculator').",
    parameters={
        "application_name": {
            "type": "string",
            "description": "Name of the application to open."
        }
    },
    required=["application_name"],
    risk_level=0
)
def open_application(application_name: str) -> Dict[str, Any]:
    app_lower = application_name.lower().strip()
    target_cmd = _discover_windows_app(app_lower) or application_name

    logger.info(f"Launching application target: {target_cmd}")

    try:
        if target_cmd.endswith(":") or target_cmd.startswith("ms-"):
            # Windows URI Protocol
            os.system(f"start {target_cmd}")
            return {"status": "success", "message": f"Opened {application_name}."}

        # Launch using Windows start/shell command
        os.startfile(target_cmd)
        return {"status": "success", "message": f"Opened {application_name}."}
    except Exception as e:
        # Fallback to subprocess
        try:
            subprocess.Popen(target_cmd, shell=True)
            return {"status": "success", "message": f"Opened {application_name}."}
        except Exception as err:
            logger.error(f"Failed to open application '{application_name}': {err}")
            return {"status": "error", "message": f"Could not find or open {application_name}."}


@tool_registry.register(
    name="close_application",
    description="Close or terminate a running process by application name.",
    parameters={
        "application_name": {
            "type": "string",
            "description": "Name of the process/application to close (e.g. 'paint', 'notepad', 'chrome')."
        }
    },
    required=["application_name"],
    risk_level=2
)
def close_application(application_name: str) -> Dict[str, Any]:
    target = application_name.lower().replace(" app", "").replace(".exe", "").strip()
    target_exe = COMMON_APP_MAPPINGS.get(target, target).replace(".exe", "")

    closed_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower().replace(".exe", "")
            if target == proc_name or target_exe == proc_name or target in proc_name:
                proc.terminate()
                closed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if closed_count > 0:
        return {"status": "success", "message": f"Closed {closed_count} instance(s) of {application_name}."}
    return {"status": "warning", "message": f"No running instances found for {application_name}."}
