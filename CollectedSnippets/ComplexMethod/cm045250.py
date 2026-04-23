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
        create_params = self._process_create_args(
            messages,
            tools,
            tool_choice,
            json_output,
            extra_create_args,
        )
        future: Union[Task[ParsedChatCompletion[BaseModel]], Task[ChatCompletion]]
        if create_params.response_format is not None:
            # Use beta client if response_format is not None
            future = asyncio.ensure_future(
                self._client.beta.chat.completions.parse(
                    messages=create_params.messages,
                    tools=(create_params.tools if len(create_params.tools) > 0 else NOT_GIVEN),
                    response_format=create_params.response_format,
                    **create_params.create_args,
                )
            )
        else:
            # Use the regular client
            future = asyncio.ensure_future(
                self._client.chat.completions.create(
                    messages=create_params.messages,
                    stream=False,
                    tools=(create_params.tools if len(create_params.tools) > 0 else NOT_GIVEN),
                    **create_params.create_args,
                )
            )

        if cancellation_token is not None:
            cancellation_token.link_future(future)
        result: Union[ParsedChatCompletion[BaseModel], ChatCompletion] = await future
        if create_params.response_format is not None:
            result = cast(ParsedChatCompletion[Any], result)

        # Handle the case where OpenAI API might return None for token counts
        # even when result.usage is not None
        usage = RequestUsage(
            # TODO backup token counting
            prompt_tokens=getattr(result.usage, "prompt_tokens", 0) if result.usage is not None else 0,
            completion_tokens=getattr(result.usage, "completion_tokens", 0) if result.usage is not None else 0,
        )

        logger.info(
            LLMCallEvent(
                messages=cast(List[Dict[str, Any]], create_params.messages),
                response=result.model_dump(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                tools=create_params.tools,
            )
        )

        if self._resolved_model is not None:
            if self._resolved_model != result.model:
                warnings.warn(
                    f"Resolved model mismatch: {self._resolved_model} != {result.model}. "
                    "Model mapping in autogen_ext.models.openai may be incorrect. "
                    f"Set the model to {result.model} to enhance token/cost estimation and suppress this warning.",
                    stacklevel=2,
                )

        # Limited to a single choice currently.
        choice: Union[ParsedChoice[Any], ParsedChoice[BaseModel], Choice] = result.choices[0]

        # Detect whether it is a function call or not.
        # We don't rely on choice.finish_reason as it is not always accurate, depending on the API used.
        content: Union[str, List[FunctionCall]]
        thought: str | None = None
        if choice.message.function_call is not None:
            raise ValueError("function_call is deprecated and is not supported by this model client.")
        elif choice.message.tool_calls is not None and len(choice.message.tool_calls) > 0:
            if choice.finish_reason != "tool_calls":
                warnings.warn(
                    f"Finish reason mismatch: {choice.finish_reason} != tool_calls "
                    "when tool_calls are present. Finish reason may not be accurate. "
                    "This may be due to the API used that is not returning the correct finish reason.",
                    stacklevel=2,
                )
            if choice.message.content is not None and choice.message.content != "":
                # Put the content in the thought field.
                thought = choice.message.content
            # NOTE: If OAI response type changes, this will need to be updated
            content = []
            for tool_call in choice.message.tool_calls:
                if not isinstance(tool_call.function.arguments, str):
                    warnings.warn(
                        f"Tool call function arguments field is not a string: {tool_call.function.arguments}."
                        "This is unexpected and may due to the API used not returning the correct type. "
                        "Attempting to convert it to string.",
                        stacklevel=2,
                    )
                    if isinstance(tool_call.function.arguments, dict):
                        tool_call.function.arguments = json.dumps(tool_call.function.arguments)
                content.append(
                    FunctionCall(
                        id=tool_call.id,
                        arguments=tool_call.function.arguments,
                        name=normalize_name(tool_call.function.name),
                    )
                )
            finish_reason = "tool_calls"
        else:
            # if not tool_calls, then it is a text response and we populate the content and thought fields.
            finish_reason = choice.finish_reason
            content = choice.message.content or ""
            # if there is a reasoning_content field, then we populate the thought field. This is for models such as R1 - direct from deepseek api.
            if choice.message.model_extra is not None:
                reasoning_content = choice.message.model_extra.get("reasoning_content")
                if reasoning_content is not None:
                    thought = reasoning_content

        logprobs: Optional[List[ChatCompletionTokenLogprob]] = None
        if choice.logprobs and choice.logprobs.content:
            logprobs = [
                ChatCompletionTokenLogprob(
                    token=x.token,
                    logprob=x.logprob,
                    top_logprobs=[TopLogprob(logprob=y.logprob, bytes=y.bytes) for y in x.top_logprobs],
                    bytes=x.bytes,
                )
                for x in choice.logprobs.content
            ]

        #   This is for local R1 models.
        if isinstance(content, str) and self._model_info["family"] == ModelFamily.R1 and thought is None:
            thought, content = parse_r1_content(content)

        response = CreateResult(
            finish_reason=normalize_stop_reason(finish_reason),
            content=content,
            usage=usage,
            cached=False,
            logprobs=logprobs,
            thought=thought,
        )

        self._total_usage = _add_usage(self._total_usage, usage)
        self._actual_usage = _add_usage(self._actual_usage, usage)

        # TODO - why is this cast needed?
        return response