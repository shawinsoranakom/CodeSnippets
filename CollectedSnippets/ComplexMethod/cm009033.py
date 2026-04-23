def _process_selection_response(
        self,
        response: dict[str, Any],
        available_tools: list[BaseTool],
        valid_tool_names: list[str],
        request: ModelRequest[ContextT],
    ) -> ModelRequest[ContextT]:
        """Process the selection response and return filtered `ModelRequest`."""
        selected_tool_names: list[str] = []
        invalid_tool_selections = []

        for tool_name in response["tools"]:
            if tool_name not in valid_tool_names:
                invalid_tool_selections.append(tool_name)
                continue

            # Only add if not already selected and within max_tools limit
            if tool_name not in selected_tool_names and (
                self.max_tools is None or len(selected_tool_names) < self.max_tools
            ):
                selected_tool_names.append(tool_name)

        if invalid_tool_selections:
            msg = f"Model selected invalid tools: {invalid_tool_selections}"
            raise ValueError(msg)

        # Filter tools based on selection and append always-included tools
        selected_tools: list[BaseTool] = [
            tool for tool in available_tools if tool.name in selected_tool_names
        ]
        always_included_tools: list[BaseTool] = [
            tool
            for tool in request.tools
            if not isinstance(tool, dict) and tool.name in self.always_include
        ]
        selected_tools.extend(always_included_tools)

        # Also preserve any provider-specific tool dicts from the original request
        provider_tools = [tool for tool in request.tools if isinstance(tool, dict)]

        return request.override(tools=[*selected_tools, *provider_tools])