import os
import shutil
from typing import Dict, Any, List
from pathlib import Path
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tools.files")

def _resolve_user_path(path_str: str) -> Path:
    """Resolves shortcuts like 'Desktop', 'Downloads', '~', etc."""
    user_home = Path.home()
    clean = path_str.strip()
    
    desktop = user_home / "Desktop"
    downloads = user_home / "Downloads"
    documents = user_home / "Documents"

    if clean.lower().startswith("desktop/"):
        return desktop / clean[8:]
    elif clean.lower() == "desktop":
        return desktop
    elif clean.lower().startswith("downloads/"):
        return downloads / clean[10:]
    elif clean.lower() == "downloads":
        return downloads
    elif clean.lower().startswith("documents/"):
        return documents / clean[10:]
    elif clean.lower() == "documents":
        return documents
    
    return Path(os.path.expanduser(clean)).resolve()

@tool_registry.register(
    name="create_folder",
    description="Create a new folder or directory at the specified location (e.g. 'Desktop/MyProjects').",
    parameters={
        "folder_path": {
            "type": "string",
            "description": "Path of the folder to create (e.g. 'Desktop/Projects', 'Downloads/Audio')."
        }
    },
    required=["folder_path"],
    risk_level=1
)
def create_folder(folder_path: str) -> Dict[str, Any]:
    target = _resolve_user_path(folder_path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created folder: {target}")
        return {"status": "success", "message": f"Folder created at {target}."}
    except Exception as e:
        logger.error(f"Failed to create folder '{folder_path}': {e}")
        return {"status": "error", "message": f"Could not create folder: {str(e)}"}


@tool_registry.register(
    name="create_file",
    description="Create a text file with optional content.",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path of the file to create (e.g. 'Desktop/notes.txt')."
        },
        "content": {
            "type": "string",
            "description": "Initial text content to write into the file."
        }
    },
    required=["file_path"],
    risk_level=1
)
def create_file(file_path: str, content: str = "") -> Dict[str, Any]:
    target = _resolve_user_path(file_path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info(f"Created file: {target}")
        return {"status": "success", "message": f"File created at {target}."}
    except Exception as e:
        logger.error(f"Failed to create file '{file_path}': {e}")
        return {"status": "error", "message": f"Could not create file: {str(e)}"}


@tool_registry.register(
    name="delete_file",
    description="Delete a file or folder permanently. (Dangerous action - requires user confirmation)",
    parameters={
        "path": {
            "type": "string",
            "description": "Path to the file or directory to delete."
        }
    },
    required=["path"],
    risk_level=3
)
def delete_file(path: str) -> Dict[str, Any]:
    target = _resolve_user_path(path)
    if not target.exists():
        return {"status": "warning", "message": f"Path '{path}' does not exist."}
    
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        logger.info(f"Deleted path: {target}")
        return {"status": "success", "message": f"Successfully deleted {target}."}
    except Exception as e:
        logger.error(f"Failed to delete '{path}': {e}")
        return {"status": "error", "message": f"Could not delete: {str(e)}"}
