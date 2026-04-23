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
        extra_create_args_keys = set(extra_create_args.keys())
        if not create_kwargs.issuperset(extra_create_args_keys):
            raise ValueError(f"Extra create args are invalid: {extra_create_args_keys - create_kwargs}")

        create_args: Dict[str, Any] = self._create_args.copy()
        create_args.update(extra_create_args)

        self._validate_model_info(messages, tools, json_output, create_args)

        # azure_messages = [to_azure_message(m) for m in messages]
        azure_messages_nested = [to_azure_message(msg) for msg in messages]
        azure_messages = [item for sublist in azure_messages_nested for item in sublist]

        if len(tools) > 0:
            if isinstance(tool_choice, Tool):
                create_args["tool_choice"] = ChatCompletionsNamedToolChoice(
                    function=ChatCompletionsNamedToolChoiceFunction(name=tool_choice.name)
                )
            else:
                create_args["tool_choice"] = tool_choice
            converted_tools = convert_tools(tools)
            task = asyncio.create_task(
                self._client.complete(messages=azure_messages, tools=converted_tools, stream=True, **create_args)
            )
        else:
            task = asyncio.create_task(self._client.complete(messages=azure_messages, stream=True, **create_args))

        if cancellation_token is not None:
            cancellation_token.link_future(task)

        # result: ChatCompletions = await task
        finish_reason: Optional[FinishReasons] = None
        content_deltas: List[str] = []
        full_tool_calls: Dict[str, FunctionCall] = {}
        prompt_tokens = 0
        completion_tokens = 0
        chunk: Optional[StreamingChatCompletionsUpdate] = None
        choice: Optional[StreamingChatChoiceUpdate] = None
        first_chunk = True
        thought = None

        async for chunk in await task:  # type: ignore
            if first_chunk:
                first_chunk = False
                # Emit the start event.
                logger.info(
                    LLMStreamStartEvent(
                        messages=[m.as_dict() for m in azure_messages],
                    )
                )
            assert isinstance(chunk, StreamingChatCompletionsUpdate)
            choice = chunk.choices[0] if len(chunk.choices) > 0 else None
            if choice and choice.finish_reason is not None:
                if isinstance(choice.finish_reason, CompletionsFinishReason):
                    finish_reason = cast(FinishReasons, choice.finish_reason.value)
                    # Handle special case for TOOL_CALLS finish reason
                    if choice.finish_reason is CompletionsFinishReason.TOOL_CALLS:
                        finish_reason = "function_calls"
                else:
                    if choice.finish_reason in ["stop", "length", "function_calls", "content_filter", "unknown"]:
                        finish_reason = choice.finish_reason  # type: ignore
                    else:
                        raise ValueError(f"Unexpected finish reason: {choice.finish_reason}")

            # We first try to load the content
            if choice and choice.delta.content is not None:
                content_deltas.append(choice.delta.content)
                yield choice.delta.content
            # Otherwise, we try to load the tool calls
            if choice and choice.delta.tool_calls is not None:
                for tool_call_chunk in choice.delta.tool_calls:
                    # print(tool_call_chunk)
                    if "index" in tool_call_chunk:
                        idx = tool_call_chunk["index"]
                    else:
                        idx = tool_call_chunk.id
                    if idx not in full_tool_calls:
                        full_tool_calls[idx] = FunctionCall(id="", arguments="", name="")

                    full_tool_calls[idx].id += tool_call_chunk.id
                    full_tool_calls[idx].name += tool_call_chunk.function.name
                    full_tool_calls[idx].arguments += tool_call_chunk.function.arguments

        if chunk and chunk.usage:
            prompt_tokens = chunk.usage.prompt_tokens

        if finish_reason is None:
            raise ValueError("No stop reason found")

        content: Union[str, List[FunctionCall]]

        if len(content_deltas) > 1:
            content = "".join(content_deltas)
            if chunk and chunk.usage:
                completion_tokens = chunk.usage.completion_tokens
            else:
                completion_tokens = 0
        else:
            content = list(full_tool_calls.values())

            if len(content_deltas) > 0:
                thought = "".join(content_deltas)

        usage = RequestUsage(
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
        )

        if isinstance(content, str) and self._model_info["family"] == ModelFamily.R1:
            thought, content = parse_r1_content(content)

        result = CreateResult(
            finish_reason=finish_reason,
            content=content,
            usage=usage,
            cached=False,
            thought=thought,
        )

        # Log the end of the stream.
        logger.info(
            LLMStreamEndEvent(
                response=result.model_dump(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        )

        self.add_usage(usage)

        yield result