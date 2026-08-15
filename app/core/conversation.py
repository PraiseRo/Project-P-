from typing import List, Dict, Any, Optional

class ConversationManager:
    """Manages short-term conversation context, user messages, and system instructions."""

    def __init__(self, system_prompt: str, max_messages: int = 15):
        self.system_prompt = system_prompt
        self.max_messages = max_messages
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})
        self._trim_history()

    def add_assistant_message(self, content: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None):
        msg: Dict[str, Any] = {"role": "assistant"}
        if content:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.history.append(msg)
        self._trim_history()

    def add_tool_result(self, tool_call_id: str, name: str, result: Any):
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": str(result)
        })
        self._trim_history()

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.history

    def clear(self):
        self.history = [{"role": "system", "content": self.system_prompt}]

    def _trim_history(self):
        # Keep system prompt plus the last max_messages
        if len(self.history) > (self.max_messages + 1):
            self.history = [self.history[0]] + self.history[-self.max_messages:]
