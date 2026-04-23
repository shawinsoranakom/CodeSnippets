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
        future = asyncio.ensure_future(
            self._client.chat(  # type: ignore
                # model=self._model_name,
                messages=create_params.messages,
                tools=create_params.tools if len(create_params.tools) > 0 else None,
                stream=False,
                format=create_params.format,
                **create_params.create_args,
            )
        )
        if cancellation_token is not None:
            cancellation_token.link_future(future)
        result: ChatResponse = await future

        usage = RequestUsage(
            # TODO backup token counting
            prompt_tokens=result.prompt_eval_count if result.prompt_eval_count is not None else 0,
            completion_tokens=(result.eval_count if result.eval_count is not None else 0),
        )

        logger.info(
            LLMCallEvent(
                messages=[m.model_dump() for m in create_params.messages],
                response=result.model_dump(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        )

        if self._resolved_model is not None:
            if self._resolved_model != result.model:
                warnings.warn(
                    f"Resolved model mismatch: {self._resolved_model} != {result.model}. "
                    "Model mapping in autogen_ext.models.openai may be incorrect.",
                    stacklevel=2,
                )

        # Detect whether it is a function call or not.
        # We don't rely on choice.finish_reason as it is not always accurate, depending on the API used.
        content: Union[str, List[FunctionCall]]
        thought: Optional[str] = None
        if result.message.tool_calls is not None:
            if result.message.content is not None and result.message.content != "":
                thought = result.message.content
            # NOTE: If OAI response type changes, this will need to be updated
            content = [
                FunctionCall(
                    id=str(self._tool_id),
                    arguments=json.dumps(x.function.arguments),
                    name=normalize_name(x.function.name),
                )
                for x in result.message.tool_calls
            ]
            finish_reason = "tool_calls"
            self._tool_id += 1
        else:
            finish_reason = result.done_reason or ""
            content = result.message.content or ""

        # Ollama currently doesn't provide these.
        # Currently open ticket: https://github.com/ollama/ollama/issues/2415
        # logprobs: Optional[List[ChatCompletionTokenLogprob]] = None
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
        response = CreateResult(
            finish_reason=normalize_stop_reason(finish_reason),
            content=content,
            usage=usage,
            cached=False,
            logprobs=None,
            thought=thought,
        )

        self._total_usage = _add_usage(self._total_usage, usage)
        self._actual_usage = _add_usage(self._actual_usage, usage)

        return response