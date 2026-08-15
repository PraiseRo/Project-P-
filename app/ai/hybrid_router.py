import re
from typing import Optional, Dict, Any, Tuple

# Conversational filler prefixes and polite noise to strip
FILLER_PREFIXES = [
    r"^hey\s+(?:p|assistant|computer)?\s*,?\s*",
    r"^please\s+,?\s*",
    r"^can\s+you\s+(?:please\s+)?(?:go\s+ahead\s+and\s+)?",
    r"^could\s+you\s+(?:please\s+)?",
    r"^would\s+you\s+(?:mind\s+)?",
    r"^i\s+want\s+you\s+to\s+",
    r"^i\s+need\s+you\s+to\s+",
    r"^help\s+me\s+(?:to\s+)?",
    r"^just\s+",
]

def clean_spoken_input(text: str) -> str:
    """Cleans conversational noise, polite filler phrases, and extra punctuation."""
    cleaned = text.lower().strip().strip(".?!,")
    # Repeatedly clean matching prefixes
    changed = True
    while changed:
        changed = False
        for pattern in FILLER_PREFIXES:
            new_val = re.sub(pattern, "", cleaned).strip().lstrip(",").strip()
            if new_val != cleaned:
                cleaned = new_val
                changed = True
    return cleaned

class LocalIntentRouter:
    """
    Enhanced fuzzy offline pattern matcher for local PC commands.
    Tolerates filler words, conversational phrasing, and accents.
    """

    @staticmethod
    def match_local_command(text: str) -> Optional[Tuple[str, Dict[str, Any], str]]:
        t = clean_spoken_input(text)

        # 1. System Metrics & Status
        if any(phrase in t for phrase in ["cpu usage", "cpu", "memory usage", "ram", "system info", "specs", "system status", "how much ram", "how much cpu"]):
            return "get_system_info", {}, "Checking your PC system metrics."

        # 2. Screenshot
        if any(phrase in t for phrase in ["take screenshot", "take a screenshot", "capture screen", "screenshot", "screen shot", "snap screen"]):
            return "take_screenshot", {}, "Taking a screenshot of your screen."

        # 3. Open Application / Tools (Handles "open paint app", "launch my calc", "start paint", etc.)
        open_match = re.match(r'^(?:open|launch|start|run|bring\s+up|open\s+up)\s+(?:the\s+|my\s+)?([a-zA-Z0-9\s_-]+)$', t)
        if open_match:
            raw_target = open_match.group(1).strip()
            # Clean trailing words like "app", "application", "program"
            app_target = re.sub(r'\s+(?:app|application|program)$', '', raw_target).strip()

            # Check web URLs
            if any(app_target.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".dev", ".gov", ".ai", ".co"]):
                return "open_url", {"url": app_target}, f"Opening {app_target} in your browser."
            if app_target.lower() in ["youtube", "google", "github", "reddit", "twitter", "x"]:
                return "open_url", {"url": f"https://{app_target.lower()}.com"}, f"Opening {app_target} in your browser."
            
            return "open_application", {"application_name": app_target}, f"Opening {app_target}."

        # 4. Close Application
        close_match = re.match(r'^(?:close|terminate|kill|quit|stop|exit)\s+(?:the\s+|my\s+)?([a-zA-Z0-9\s_-]+)$', t)
        if close_match:
            raw_target = close_match.group(1).strip()
            app_target = re.sub(r'\s+(?:app|application|program)$', '', raw_target).strip()
            return "close_application", {"application_name": app_target}, f"Closing {app_target}."

        # 5. Search Web / YouTube
        search_yt = re.match(r'^(?:search\s+youtube\s+for|search\s+for\s+.*\s+on\s+youtube|play\s+.*\s+on\s+youtube)\s+(.+)$', t)
        if search_yt:
            return "search_web", {"query": search_yt.group(1).strip(), "engine": "youtube"}, f"Searching YouTube for {search_yt.group(1)}."

        search_google = re.match(r'^(?:search\s+google\s+for|search\s+web\s+for|search\s+for|google|lookup)\s+(.+)$', t)
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
