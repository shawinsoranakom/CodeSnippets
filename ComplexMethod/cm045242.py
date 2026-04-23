async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        tool_choice: Tool | Literal["auto", "required", "none"] = "auto",
        json_output: Optional[bool | type[BaseModel]] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """Create a chat completion using the Semantic Kernel client.

        The `extra_create_args` dictionary can include two special keys:

        1) `"kernel"` (optional):
            An instance of :class:`semantic_kernel.Kernel` used to execute the request.
            If not provided either in constructor or extra_create_args, a ValueError is raised.

        2) `"prompt_execution_settings"` (optional):
            An instance of a :class:`PromptExecutionSettings` subclass corresponding to the
            underlying Semantic Kernel client (e.g., `AzureChatPromptExecutionSettings`,
            `GoogleAIChatPromptExecutionSettings`). If not provided, the adapter's default
            prompt settings will be used.

        Args:
            messages: The list of LLM messages to send.
            tools: The tools that may be invoked during the chat.
            json_output: Whether the model is expected to return JSON.
            extra_create_args: Additional arguments to control the chat completion behavior.
            cancellation_token: Token allowing cancellation of the request.

        Returns:
            CreateResult: The result of the chat completion.
        """
        if isinstance(json_output, type) and issubclass(json_output, BaseModel):
            raise ValueError("structured output is not currently supported in SKChatCompletionAdapter")

        # Handle tool_choice parameter
        if tool_choice != "auto":
            warnings.warn(
                "tool_choice parameter is specified but may not be fully supported by SKChatCompletionAdapter.",
                stacklevel=2,
            )

        kernel = self._get_kernel(extra_create_args)

        chat_history = self._convert_to_chat_history(messages)
        user_settings = self._get_prompt_settings(extra_create_args)
        settings = self._build_execution_settings(user_settings, tools)

        # Sync tools with kernel
        self._sync_tools_with_kernel(kernel, tools)

        result = await self._sk_client.get_chat_message_contents(chat_history, settings=settings, kernel=kernel)
        # Track token usage from result metadata
        prompt_tokens = 0
        completion_tokens = 0

        if result[0].metadata and "usage" in result[0].metadata:
            usage = result[0].metadata["usage"]
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)

        logger.info(
            LLMCallEvent(
                messages=[msg.model_dump() for msg in chat_history],
                response=ensure_serializable(result[0]).model_dump(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )

        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

        # Process content based on whether there are tool calls
        content: Union[str, list[FunctionCall]]
        if any(isinstance(item, FunctionCallContent) for item in result[0].items):
            content = self._process_tool_calls(result[0])
            finish_reason: Literal["function_calls", "stop"] = "function_calls"
        else:
            content = result[0].content
            finish_reason = "stop"

        if isinstance(content, str) and self._model_info["family"] == ModelFamily.R1:
            thought, content = parse_r1_content(content)
        else:
            thought = None

        return CreateResult(
            content=content,
            finish_reason=finish_reason,
            usage=RequestUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            cached=False,
            thought=thought,
        )