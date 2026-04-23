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
        # Make sure all extra_create_args are valid
        # TODO: kwarg checking logic
        # extra_create_args_keys = set(extra_create_args.keys())
        # if not create_kwargs.issuperset(extra_create_args_keys):
        #     raise ValueError(f"Extra create args are invalid: {extra_create_args_keys - create_kwargs}")
        create_params = self._process_create_args(
            messages,
            tools,
            tool_choice,
            json_output,
            extra_create_args,
        )
        stream_future = asyncio.ensure_future(
            self._client.chat(  # type: ignore
                # model=self._model_name,
                messages=create_params.messages,
                tools=create_params.tools if len(create_params.tools) > 0 else None,
                stream=True,
                format=create_params.format,
                **create_params.create_args,
            )
        )
        if cancellation_token is not None:
            cancellation_token.link_future(stream_future)
        stream = await stream_future

        chunk = None
        stop_reason = None
        content_chunks: List[str] = []
        full_tool_calls: List[FunctionCall] = []
        completion_tokens = 0
        first_chunk = True
        while True:
            try:
                chunk_future = asyncio.ensure_future(anext(stream))
                if cancellation_token is not None:
                    cancellation_token.link_future(chunk_future)
                chunk = await chunk_future

                if first_chunk:
                    first_chunk = False
                    # Emit the start event.
                    logger.info(
                        LLMStreamStartEvent(
                            messages=[m.model_dump() for m in create_params.messages],
                        )
                    )
                # set the stop_reason for the usage chunk to the prior stop_reason
                stop_reason = chunk.done_reason if chunk.done and stop_reason is None else stop_reason
                # First try get content
                if chunk.message.content is not None:
                    content_chunks.append(chunk.message.content)
                    if len(chunk.message.content) > 0:
                        yield chunk.message.content

                # Get tool calls
                if chunk.message.tool_calls is not None:
                    full_tool_calls.extend(
                        [
                            FunctionCall(
                                id=str(self._tool_id),
                                arguments=json.dumps(x.function.arguments),
                                name=normalize_name(x.function.name),
                            )
                            for x in chunk.message.tool_calls
                        ]
                    )

                # TODO: logprobs currently unsupported in ollama.
                # See: https://github.com/ollama/ollama/issues/2415
                # if choice.logprobs and choice.logprobs.content:
                #     logprobs = [
                #         ChatCompletionTokenLogprob(
                #             token=x.token,
                #             logprob=x.logprob,
                #             top_logprobs=[TopLogprob(logprob=y.logprob, bytes=y.bytes) for y in x.top_logprobs],
                #             bytes=x.bytes,
                #         )
                #         for x in choice.logprobs.content
                #     ]

            except StopAsyncIteration:
                break

        if chunk and chunk.prompt_eval_count:
            prompt_tokens = chunk.prompt_eval_count
        else:
            prompt_tokens = 0

        content: Union[str, List[FunctionCall]]
        thought: Optional[str] = None

        if len(content_chunks) > 0 and len(full_tool_calls) > 0:
            content = full_tool_calls
            thought = "".join(content_chunks)
            if chunk and chunk.eval_count:
                completion_tokens = chunk.eval_count
            else:
                completion_tokens = 0
        elif len(content_chunks) > 1:
            content = "".join(content_chunks)
            if chunk and chunk.eval_count:
                completion_tokens = chunk.eval_count
            else:
                completion_tokens = 0
        else:
            completion_tokens = 0
            content = full_tool_calls

        usage = RequestUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        result = CreateResult(
            finish_reason=normalize_stop_reason(stop_reason),
            content=content,
            usage=usage,
            cached=False,
            logprobs=None,
            thought=thought,
        )

        # Emit the end event.
        logger.info(
            LLMStreamEndEvent(
                response=result.model_dump(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        )

        self._total_usage = _add_usage(self._total_usage, usage)
        self._actual_usage = _add_usage(self._actual_usage, usage)

        yield result