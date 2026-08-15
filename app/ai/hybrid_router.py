import re
from typing import Optional, Dict, Any, Tuple

class LocalIntentRouter:
    """
    Fast, deterministic offline pattern matcher for local PC commands.
    If a command matches an offline PC action (e.g. 'open notepad', 'cpu usage', 'create folder'),
    it resolves directly without needing cloud LLM calls, ensuring zero latency and 100% offline control.
    """

    @staticmethod
    def match_local_command(text: str) -> Optional[Tuple[str, Dict[str, Any], str]]:
        """
        Returns (tool_name, arguments, conversational_confirmation) if matched locally, else None.
        """
        t = text.lower().strip().strip(".?!")

        # 1. System Metrics
        if any(phrase in t for phrase in ["cpu usage", "memory usage", "system info", "specs", "system status"]):
            return "get_system_info", {}, "Checking your PC system metrics."

        # 2. Screenshot
        if any(phrase in t for phrase in ["take screenshot", "take a screenshot", "capture screen", "screenshot"]):
            return "take_screenshot", {}, "Taking a screenshot of your screen."

        # 3. Open Application
        open_match = re.match(r'^(?:open|launch|start|run)\s+([a-zA-Z0-9\s_-]+)$', t)
        if open_match:
            app_target = open_match.group(1).strip()
            # If target looks like a website, route to browser
            if any(app_target.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".dev", ".gov", ".ai", ".co"]):
                return "open_url", {"url": app_target}, f"Opening {app_target} in your browser."
            if app_target.lower() in ["youtube", "google", "github", "reddit", "twitter", "x"]:
                return "open_url", {"url": f"https://{app_target.lower()}.com"}, f"Opening {app_target} in your browser."
            return "open_application", {"application_name": app_target}, f"Opening {app_target}."

        # 4. Close Application
        close_match = re.match(r'^(?:close|terminate|kill|quit|stop)\s+([a-zA-Z0-9\s_-]+)$', t)
        if close_match:
            app_target = close_match.group(1).strip()
            return "close_application", {"application_name": app_target}, f"Closing {app_target}."

        # 5. Search Web / YouTube
        search_yt = re.match(r'^(?:search\s+youtube\s+for|search\s+for\s+.*\s+on\s+youtube)\s+(.+)$', t)
        if search_yt:
            return "search_web", {"query": search_yt.group(1).strip(), "engine": "youtube"}, f"Searching YouTube for {search_yt.group(1)}."

        search_google = re.match(r'^(?:search\s+google\s+for|search\s+web\s+for|search\s+for)\s+(.+)$', t)
        if search_google:
            return "search_web", {"query": search_google.group(1).strip(), "engine": "google"}, f"Searching Google for {search_google.group(1)}."

        # 6. Create Folder
        create_folder_match = re.match(r'^(?:create|make)\s+(?:a\s+)?folder\s+(?:called|named\s+)?([a-zA-Z0-9\s_/-]+?)(?:\s+on\s+(desktop|downloads|documents))?$', t)
        if create_folder_match:
            folder_name = create_folder_match.group(1).strip()
            location = create_folder_match.group(2)
            path = f"{location}/{folder_name}" if location else folder_name
            return "create_folder", {"folder_path": path}, f"Creating folder {folder_name}."

        return None
