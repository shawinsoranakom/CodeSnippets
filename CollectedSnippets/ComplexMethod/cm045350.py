def __init__(
        self, tools: List[BaseTool[Any, Any]], tool_overrides: Optional[Dict[str, ToolOverride]] = None
    ) -> None:
        self._tools = tools
        self._tool_overrides = tool_overrides or {}

        # Build reverse mapping from override names to original names for call_tool
        self._override_name_to_original: Dict[str, str] = {}
        existing_tool_names = {tool.name for tool in self._tools}

        for original_name, override in self._tool_overrides.items():
            if override.name and override.name != original_name:
                # Check for conflicts with existing tool names
                if override.name in existing_tool_names and override.name != original_name:
                    raise ValueError(
                        f"Tool override name '{override.name}' conflicts with existing tool name. "
                        f"Override names must not conflict with any tool names."
                    )
                # Check for conflicts with other override names
                if override.name in self._override_name_to_original:
                    existing_original = self._override_name_to_original[override.name]
                    raise ValueError(
                        f"Tool override name '{override.name}' is used by multiple tools: "
                        f"'{existing_original}' and '{original_name}'. Override names must be unique."
                    )
                self._override_name_to_original[override.name] = original_name