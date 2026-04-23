def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
        tool_choice: dict | str | Literal["auto", "any"] | None = None,  # noqa: PYI051
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Bind tool-like objects to this chat model.

        Assumes model is compatible with OpenAI tool-calling API.

        Args:
            tools: A list of tool definitions to bind to this chat model.

                Supports any tool definition handled by [`convert_to_openai_tool`][langchain_core.utils.function_calling.convert_to_openai_tool].
            tool_choice: Which tool to require the model to call.
                Must be the name of the single provided function or
                `'auto'` to automatically determine which function to call
                (if any), or a dict of the form:
                {"type": "function", "function": {"name": <<tool_name>>}}.
            kwargs: Any additional parameters are passed directly to
                `self.bind(**kwargs)`.
        """  # noqa: E501
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        if tool_choice:
            tool_names = []
            for tool in formatted_tools:
                if ("function" in tool and (name := tool["function"].get("name"))) or (
                    name := tool.get("name")
                ):
                    tool_names.append(name)
                else:
                    pass
            if tool_choice in tool_names:
                kwargs["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tool_choice},
                }
            else:
                kwargs["tool_choice"] = tool_choice
        return super().bind(tools=formatted_tools, **kwargs)