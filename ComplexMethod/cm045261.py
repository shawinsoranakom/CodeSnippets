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
        extra_create_args_keys = set(extra_create_args.keys())
        if not create_kwargs.issuperset(extra_create_args_keys):
            raise ValueError(f"Extra create args are invalid: {extra_create_args_keys - create_kwargs}")

        # Copy the create args and overwrite anything in extra_create_args
        create_args = self._create_args.copy()
        create_args.update(extra_create_args)

        self._validate_model_info(messages, tools, json_output, create_args)

        azure_messages_nested = [to_azure_message(msg) for msg in messages]
        azure_messages = [item for sublist in azure_messages_nested for item in sublist]

        task: Task[ChatCompletions]

        if len(tools) > 0:
            if isinstance(tool_choice, Tool):
                create_args["tool_choice"] = ChatCompletionsNamedToolChoice(
                    function=ChatCompletionsNamedToolChoiceFunction(name=tool_choice.name)
                )
            else:
                create_args["tool_choice"] = tool_choice
            converted_tools = convert_tools(tools)
            task = asyncio.create_task(  # type: ignore
                self._client.complete(messages=azure_messages, tools=converted_tools, **create_args)  # type: ignore
            )
        else:
            task = asyncio.create_task(  # type: ignore
                self._client.complete(  # type: ignore
                    messages=azure_messages,
                    **create_args,
                )
            )

        if cancellation_token is not None:
            cancellation_token.link_future(task)

        result: ChatCompletions = await task

        usage = RequestUsage(
            prompt_tokens=result.usage.prompt_tokens if result.usage else 0,
            completion_tokens=result.usage.completion_tokens if result.usage else 0,
        )

        logger.info(
            LLMCallEvent(
                messages=[m.as_dict() for m in azure_messages],
                response=result.as_dict(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        )

        choice = result.choices[0]
        thought = None

        if choice.finish_reason == CompletionsFinishReason.TOOL_CALLS:
            assert choice.message.tool_calls is not None
            content: Union[str, List[FunctionCall]] = [
                FunctionCall(
                    id=x.id,
                    arguments=x.function.arguments,
                    name=normalize_name(x.function.name),
                )
                for x in choice.message.tool_calls
            ]
            finish_reason = "function_calls"

            if choice.message.content:
                thought = choice.message.content
        else:
            if isinstance(choice.finish_reason, CompletionsFinishReason):
                finish_reason = choice.finish_reason.value
            else:
                finish_reason = choice.finish_reason  # type: ignore
            content = choice.message.content or ""

        if isinstance(content, str) and self._model_info["family"] == ModelFamily.R1:
            thought, content = parse_r1_content(content)

        response = CreateResult(
            finish_reason=finish_reason,  # type: ignore
            content=content,
            usage=usage,
            cached=False,
            thought=thought,
        )

        self.add_usage(usage)

        return response