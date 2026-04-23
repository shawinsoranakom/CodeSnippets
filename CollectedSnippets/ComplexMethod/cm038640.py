def _construct_harmony_system_input_message(
        self, request: ResponsesRequest, with_custom_tools: bool, tool_types: set[str]
    ) -> OpenAIHarmonyMessage:
        model_identity = self._extract_system_message_from_request(request)

        reasoning_effort = request.reasoning.effort if request.reasoning else None

        # Extract allowed_tools from MCP tool requests
        allowed_tools_map = _extract_allowed_tools_from_mcp_requests(request.tools)

        # Get filtered tool descriptions first.
        # If get_tool_description returns None (due to filtering), the tool is disabled.
        browser_description = (
            self.tool_server.get_tool_description(
                "browser", allowed_tools_map.get("web_search_preview")
            )
            if "web_search_preview" in tool_types
            and self.tool_server is not None
            and self.tool_server.has_tool("browser")
            else None
        )
        python_description = (
            self.tool_server.get_tool_description(
                "python", allowed_tools_map.get("code_interpreter")
            )
            if "code_interpreter" in tool_types
            and self.tool_server is not None
            and self.tool_server.has_tool("python")
            else None
        )
        container_description = (
            self.tool_server.get_tool_description(
                "container", allowed_tools_map.get("container")
            )
            if "container" in tool_types
            and self.tool_server is not None
            and self.tool_server.has_tool("container")
            else None
        )

        sys_msg = get_system_message(
            model_identity=model_identity,
            reasoning_effort=reasoning_effort,
            browser_description=browser_description,
            python_description=python_description,
            container_description=container_description,
            instructions=request.instructions,
            with_custom_tools=with_custom_tools,
        )
        return sys_msg