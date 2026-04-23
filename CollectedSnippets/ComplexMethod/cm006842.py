def __call__(
        self,
        messages: list[dict[str, str]],
        stop_sequences: list[str] | None = None,
        grammar: str | None = None,
        tools_to_call_from: list[Tool] | None = None,
        **kwargs,
    ) -> ChatMessage:
        """Process messages through the LangChain model and return Hugging Face format.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            stop_sequences: Optional list of strings to stop generation
            grammar: Optional grammar specification (not used)
            tools_to_call_from: Optional list of available tools (not used)
            **kwargs: Additional arguments passed to the LangChain model

        Returns:
            ChatMessage: Response in Hugging Face format
        """
        if grammar:
            msg = "Grammar is not yet supported."
            raise ValueError(msg)

        # Convert HF messages to LangChain messages
        lc_messages = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                # Default any unknown role to "user"
                lc_messages.append(HumanMessage(content=content))

        # Convert tools to LangChain tools
        if tools_to_call_from:
            tools_to_call_from = [_hf_tool_to_lc_tool(tool) for tool in tools_to_call_from]

        model = self.chat_model.bind_tools(tools_to_call_from) if tools_to_call_from else self.chat_model

        # Call the LangChain model
        result_msg: AIMessage = model.invoke(lc_messages, stop=stop_sequences, **kwargs)

        # Convert the AIMessage into an HF ChatMessage
        return ChatMessage(
            role="assistant",
            content=result_msg.content or "",
            tool_calls=[_lc_tool_call_to_hf_tool_call(tool_call) for tool_call in result_msg.tool_calls],
        )