async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        tool_choice: Tool | Literal["auto", "required", "none"] = "auto",
        json_output: Optional[bool | type[BaseModel]] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        """Create a streaming chat completion using the Semantic Kernel client.

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

        Yields:
            Union[str, CreateResult]: Either a string chunk of the response or a CreateResult containing function calls.
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
        self._sync_tools_with_kernel(kernel, tools)

        prompt_tokens = 0
        completion_tokens = 0
        accumulated_text = ""

        # Keep track of in-progress function calls. Keyed by ID
        # because partial chunks for the same function call might arrive separately.
        function_calls_in_progress: dict[str, FunctionCallContent] = {}

        # Track the ID of the last function call we saw so we can continue
        # accumulating chunk arguments for that call if new items have id=None
        last_function_call_id: Optional[str] = None

        first_chunk = True

        async for streaming_messages in self._sk_client.get_streaming_chat_message_contents(
            chat_history, settings=settings, kernel=kernel
        ):
            if first_chunk:
                first_chunk = False
                # Emit the start event.
                logger.info(
                    LLMStreamStartEvent(
                        messages=[msg.model_dump() for msg in chat_history],
                    )
                )
            for msg in streaming_messages:
                # Track token usage
                if msg.metadata and "usage" in msg.metadata:
                    usage = msg.metadata["usage"]
                    prompt_tokens = getattr(usage, "prompt_tokens", 0)
                    completion_tokens = getattr(usage, "completion_tokens", 0)

                # Process function call deltas
                for item in msg.items:
                    if isinstance(item, FunctionCallContent):
                        # If the chunk has a valid ID, we start or continue that ID explicitly
                        if item.id:
                            last_function_call_id = item.id
                            if last_function_call_id not in function_calls_in_progress:
                                function_calls_in_progress[last_function_call_id] = item
                            else:
                                # Merge partial arguments into existing call
                                existing_call = function_calls_in_progress[last_function_call_id]
                                self._merge_function_call_content(existing_call, item)
                        else:
                            # item.id is None, so we assume it belongs to the last known ID
                            if not last_function_call_id:
                                # No call in progress means we can't merge
                                # You could either skip or raise an error here
                                warnings.warn(
                                    "Received function call chunk with no ID and no call in progress.", stacklevel=2
                                )
                                continue

                            existing_call = function_calls_in_progress[last_function_call_id]
                            # Merge partial chunk
                            self._merge_function_call_content(existing_call, item)

                # Check if the model signaled tool_calls finished
                if msg.finish_reason == "tool_calls" and function_calls_in_progress:
                    calls_to_yield: list[FunctionCall] = []
                    for _, call_content in function_calls_in_progress.items():
                        plugin_name = call_content.plugin_name or ""
                        function_name = call_content.function_name
                        if plugin_name:
                            full_name = f"{plugin_name}-{function_name}"
                        else:
                            full_name = function_name

                        if isinstance(call_content.arguments, dict):
                            arguments = json.dumps(call_content.arguments)
                        else:
                            assert isinstance(call_content.arguments, str)
                            arguments = call_content.arguments or "{}"

                        calls_to_yield.append(
                            FunctionCall(
                                id=call_content.id or "unknown_id",
                                name=full_name,
                                arguments=arguments,
                            )
                        )
                    # Yield all function calls in progress
                    yield CreateResult(
                        content=calls_to_yield,
                        finish_reason="function_calls",
                        usage=RequestUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
                        cached=False,
                    )
                    return

                # Handle any plain text in the message
                if msg.content:
                    accumulated_text += msg.content
                    yield msg.content

        # If we exit the loop without tool calls finishing, yield whatever text was accumulated
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

        thought = None
        if isinstance(accumulated_text, str) and self._model_info["family"] == ModelFamily.R1:
            thought, accumulated_text = parse_r1_content(accumulated_text)

        result = CreateResult(
            content=accumulated_text,
            finish_reason="stop",
            usage=RequestUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            cached=False,
            thought=thought,
        )

        # Emit the end event.
        logger.info(
            LLMStreamEndEvent(
                response=result.model_dump(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )

        yield result