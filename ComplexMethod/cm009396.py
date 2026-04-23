def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type[BaseModel] | Callable | BaseTool],
        *,
        tool_choice: dict | str | bool | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Bind tool-like objects to this chat model.

        Assumes model is compatible with Fireworks tool-calling API.

        Args:
            tools: A list of tool definitions to bind to this chat model.

                Supports any tool definition handled by [`convert_to_openai_tool`][langchain_core.utils.function_calling.convert_to_openai_tool].
            tool_choice: Which tool to require the model to call.
                Must be the name of the single provided function,
                `'auto'` to automatically determine which function to call
                with the option to not call any function, `'any'` to enforce that some
                function is called, or a dict of the form:
                `{"type": "function", "function": {"name": <<tool_name>>}}`.
            **kwargs: Any additional parameters to pass to
                `langchain_fireworks.chat_models.ChatFireworks.bind`
        """  # noqa: E501
        strict = kwargs.pop("strict", None)
        formatted_tools = [
            convert_to_openai_tool(tool, strict=strict) for tool in tools
        ]
        if tool_choice is not None and tool_choice:
            if isinstance(tool_choice, str) and (
                tool_choice not in ("auto", "any", "none")
            ):
                tool_choice = {"type": "function", "function": {"name": tool_choice}}
            if isinstance(tool_choice, bool):
                if len(tools) > 1:
                    msg = (
                        "tool_choice can only be True when there is one tool. Received "
                        f"{len(tools)} tools."
                    )
                    raise ValueError(msg)
                tool_name = formatted_tools[0]["function"]["name"]
                tool_choice = {
                    "type": "function",
                    "function": {"name": tool_name},
                }

            kwargs["tool_choice"] = tool_choice
        return super().bind(tools=formatted_tools, **kwargs)