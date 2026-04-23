def bind_tools(
        self,
        tools: Sequence[Mapping[str, Any] | type | Callable | BaseTool],
        *,
        tool_choice: dict[str, str] | str | None = None,
        parallel_tool_calls: bool | None = None,
        strict: bool | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        r"""Bind tool-like objects to `ChatAnthropic`.

        Args:
            tools: A list of tool definitions to bind to this chat model.

                Supports Anthropic format tool schemas and any tool definition handled
                by [`convert_to_openai_tool`][langchain_core.utils.function_calling.convert_to_openai_tool].
            tool_choice: Which tool to require the model to call. Options are:

                - Name of the tool as a string or as dict `{"type": "tool", "name": "<<tool_name>>"}`: calls corresponding tool
                - `'auto'`, `{"type: "auto"}`, or `None`: automatically selects a tool (including no tool)
                - `'any'` or `{"type: "any"}`: force at least one tool to be called
            parallel_tool_calls: Set to `False` to disable parallel tool use.

                Defaults to `None` (no specification, which allows parallel tool use).

                !!! version-added "Added in `langchain-anthropic` 0.3.2"
            strict: If `True`, Claude's schema adherence is applied to tool calls.

                See the [docs](https://docs.langchain.com/oss/python/integrations/chat/anthropic#strict-tool-use) for more info.
            kwargs: Any additional parameters are passed directly to `bind`.

        Example:
            ```python
            from langchain_anthropic import ChatAnthropic
            from pydantic import BaseModel, Field


            class GetWeather(BaseModel):
                '''Get the current weather in a given location'''

                location: str = Field(..., description="The city and state, e.g. San Francisco, CA")


            class GetPrice(BaseModel):
                '''Get the price of a specific product.'''

                product: str = Field(..., description="The product to look up.")


            model = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)
            model_with_tools = model.bind_tools([GetWeather, GetPrice])
            model_with_tools.invoke(
                "What is the weather like in San Francisco",
            )
            # -> AIMessage(
            #     content=[
            #         {'text': '<thinking>\nBased on the user\'s question, the relevant function to call is GetWeather, which requires the "location" parameter.\n\nThe user has directly specified the location as "San Francisco". Since San Francisco is a well known city, I can reasonably infer they mean San Francisco, CA without needing the state specified.\n\nAll the required parameters are provided, so I can proceed with the API call.\n</thinking>', 'type': 'text'},
            #         {'text': None, 'type': 'tool_use', 'id': 'toolu_01SCgExKzQ7eqSkMHfygvYuu', 'name': 'GetWeather', 'input': {'location': 'San Francisco, CA'}}
            #     ],
            #     response_metadata={'id': 'msg_01GM3zQtoFv8jGQMW7abLnhi', 'model': 'claude-sonnet-4-5-20250929', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 487, 'output_tokens': 145}},
            #     id='run-87b1331e-9251-4a68-acef-f0a018b639cc-0'
            # )
            ```
        """  # noqa: E501
        # Allows built-in tools either by their:
        # - Raw `dict` format
        # - Extracting extras["provider_tool_definition"] if provided on a BaseTool
        formatted_tools = [
            tool
            if _is_builtin_tool(tool)
            else convert_to_anthropic_tool(tool, strict=strict)
            for tool in tools
        ]
        if not tool_choice:
            pass
        elif isinstance(tool_choice, dict):
            kwargs["tool_choice"] = tool_choice
        elif isinstance(tool_choice, str) and tool_choice in ("any", "auto"):
            kwargs["tool_choice"] = {"type": tool_choice}
        elif isinstance(tool_choice, str):
            kwargs["tool_choice"] = {"type": "tool", "name": tool_choice}
        else:
            msg = (
                f"Unrecognized 'tool_choice' type {tool_choice=}. Expected dict, "
                f"str, or None."
            )
            raise ValueError(
                msg,
            )

        # Anthropic API rejects forced tool use when thinking is enabled:
        # "Thinking may not be enabled when tool_choice forces tool use."
        # Drop forced tool_choice and warn, matching the behavior in
        # _get_llm_for_structured_output_when_thinking_is_enabled.
        if (
            self.thinking is not None
            and self.thinking.get("type") in ("enabled", "adaptive")
            and "tool_choice" in kwargs
            and kwargs["tool_choice"].get("type") in ("any", "tool")
        ):
            warnings.warn(
                "tool_choice is forced but thinking is enabled. The Anthropic "
                "API does not support forced tool use with thinking. "
                "Dropping tool_choice to avoid an API error. Tool calls are "
                "not guaranteed. Consider disabling thinking or adjusting "
                "your prompt to ensure the tool is called.",
                stacklevel=2,
            )
            del kwargs["tool_choice"]

        if parallel_tool_calls is not None:
            disable_parallel_tool_use = not parallel_tool_calls
            if "tool_choice" in kwargs:
                kwargs["tool_choice"]["disable_parallel_tool_use"] = (
                    disable_parallel_tool_use
                )
            else:
                kwargs["tool_choice"] = {
                    "type": "auto",
                    "disable_parallel_tool_use": disable_parallel_tool_use,
                }

        return self.bind(tools=formatted_tools, **kwargs)