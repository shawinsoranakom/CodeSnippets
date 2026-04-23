def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
        *,
        tool_choice: dict | str | bool | None = None,
        strict: bool | None = None,
        parallel_tool_calls: bool | None = None,
        response_format: _DictOrPydanticClass | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Bind tool-like objects to this chat model.

        Assumes model is compatible with OpenAI tool-calling API.

        Args:
            tools: A list of tool definitions to bind to this chat model.

                Supports any tool definition handled by [`convert_to_openai_tool`][langchain_core.utils.function_calling.convert_to_openai_tool].
            tool_choice: Which tool to require the model to call. Options are:

                - `str` of the form `'<<tool_name>>'`: calls `<<tool_name>>` tool.
                - `'auto'`: automatically selects a tool (including no tool).
                - `'none'`: does not call a tool.
                - `'any'` or `'required'` or `True`: force at least one tool to be called.
                - `dict` of the form `{"type": "function", "function": {"name": <<tool_name>>}}`: calls `<<tool_name>>` tool.
                - `False` or `None`: no effect, default OpenAI behavior.
            strict: If `True`, model output is guaranteed to exactly match the JSON Schema
                provided in the tool definition. The input schema will also be validated according to the
                [supported schemas](https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?api-mode=responses#supported-schemas).
                If `False`, input schema will not be validated and model output will not
                be validated. If `None`, `strict` argument will not be passed to the model.
            parallel_tool_calls: Set to `False` to disable parallel tool use.
                Defaults to `None` (no specification, which allows parallel tool use).
            response_format: Optional schema to format model response. If provided
                and the model does not call a tool, the model will generate a
                [structured response](https://platform.openai.com/docs/guides/structured-outputs).
            kwargs: Any additional parameters are passed directly to `bind`.
        """  # noqa: E501
        if parallel_tool_calls is not None:
            kwargs["parallel_tool_calls"] = parallel_tool_calls
        formatted_tools = [
            convert_to_openai_tool(tool, strict=strict) for tool in tools
        ]
        for original, formatted in zip(tools, formatted_tools, strict=False):
            if (
                isinstance(original, BaseTool)
                and hasattr(original, "extras")
                and isinstance(original.extras, dict)
                and "defer_loading" in original.extras
            ):
                formatted["defer_loading"] = original.extras["defer_loading"]
        tool_names = []
        for tool in formatted_tools:
            if "function" in tool:
                tool_names.append(tool["function"]["name"])
            elif "name" in tool:
                tool_names.append(tool["name"])
            else:
                pass
        if tool_choice:
            if isinstance(tool_choice, str):
                # tool_choice is a tool/function name
                if tool_choice in tool_names:
                    tool_choice = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                elif tool_choice in WellKnownTools:
                    tool_choice = {"type": tool_choice}
                # 'any' is not natively supported by OpenAI API.
                # We support 'any' since other models use this instead of 'required'.
                elif tool_choice == "any":
                    tool_choice = "required"
                else:
                    pass
            elif isinstance(tool_choice, bool):
                tool_choice = "required"
            elif isinstance(tool_choice, dict):
                pass
            else:
                msg = (
                    f"Unrecognized tool_choice type. Expected str, bool or dict. "
                    f"Received: {tool_choice}"
                )
                raise ValueError(msg)
            kwargs["tool_choice"] = tool_choice

        if response_format:
            if (
                isinstance(response_format, dict)
                and response_format.get("type") == "json_schema"
                and "schema" in response_format.get("json_schema", {})
            ):
                # compat with langchain.agents.create_agent response_format, which is
                # an approximation of OpenAI format
                strict = response_format["json_schema"].get("strict", None)
                response_format = cast(dict, response_format["json_schema"]["schema"])
            kwargs["response_format"] = _convert_to_openai_response_format(
                response_format, strict=strict
            )
        return super().bind(tools=formatted_tools, **kwargs)