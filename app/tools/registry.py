from typing import Dict, Any, Callable, Optional, List
from pydantic import BaseModel, Field

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    risk_level: int = Field(default=0, description="0=Safe, 1=Low Risk, 2=Moderate/Destructive, 3=High Risk/Shell")
    parameters: Dict[str, Any]
    required: List[str] = Field(default_factory=list)

class ToolRegistry:
    """Central repository of callable tools available to the AI Orchestrator."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, Callable[..., Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required: Optional[List[str]] = None,
        risk_level: int = 0
    ):
        """Decorator or function to register a new tool with its execution handler."""
        def decorator(func: Callable[..., Any]):
            definition = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                required=required or [],
                risk_level=risk_level
            )
            self._tools[name] = definition
            self._executors[name] = func
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_executor(self, name: str) -> Optional[Callable[..., Any]]:
        return self._executors.get(name)

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Converts registered tools into OpenAI function calling schema format."""
        openai_tools = []
        for name, tool in self._tools.items():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required,
                        "additionalProperties": False
                    }
                }
            })
        return openai_tools

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Executes a tool by name with arguments."""
        if name not in self._executors:
            raise ValueError(f"Tool '{name}' is not registered.")
        
        executor = self._executors[name]
        import inspect
        if inspect.iscoroutinefunction(executor):
            return await executor(**arguments)
        else:
            return executor(**arguments)

# Global tool registry singleton
tool_registry = ToolRegistry()
