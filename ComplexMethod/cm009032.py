def _prepare_selection_request(
        self, request: ModelRequest[ContextT]
    ) -> _SelectionRequest | None:
        """Prepare inputs for tool selection.

        Args:
            request: the model request.

        Returns:
            `SelectionRequest` with prepared inputs, or `None` if no selection is
            needed.

        Raises:
            ValueError: If tools in `always_include` are not found in the request.
            AssertionError: If no user message is found in the request messages.
        """
        # If no tools available, return None
        if not request.tools or len(request.tools) == 0:
            return None

        # Filter to only BaseTool instances (exclude provider-specific tool dicts)
        base_tools = [tool for tool in request.tools if not isinstance(tool, dict)]

        # Validate that always_include tools exist
        if self.always_include:
            available_tool_names = {tool.name for tool in base_tools}
            missing_tools = [
                name for name in self.always_include if name not in available_tool_names
            ]
            if missing_tools:
                msg = (
                    f"Tools in always_include not found in request: {missing_tools}. "
                    f"Available tools: {sorted(available_tool_names)}"
                )
                raise ValueError(msg)

        # Separate tools that are always included from those available for selection
        available_tools = [tool for tool in base_tools if tool.name not in self.always_include]

        # If no tools available for selection, return None
        if not available_tools:
            return None

        system_message = self.system_prompt
        # If there's a max_tools limit, append instructions to the system prompt
        if self.max_tools is not None:
            system_message += (
                f"\nIMPORTANT: List the tool names in order of relevance, "
                f"with the most relevant first. "
                f"If you exceed the maximum number of tools, "
                f"only the first {self.max_tools} will be used."
            )

        # Get the last user message from the conversation history
        last_user_message: HumanMessage
        for message in reversed(request.messages):
            if isinstance(message, HumanMessage):
                last_user_message = message
                break
        else:
            msg = "No user message found in request messages"
            raise AssertionError(msg)

        model = self.model or request.model
        valid_tool_names = [tool.name for tool in available_tools]

        return _SelectionRequest(
            available_tools=available_tools,
            system_message=system_message,
            last_user_message=last_user_message,
            model=model,
            valid_tool_names=valid_tool_names,
        )