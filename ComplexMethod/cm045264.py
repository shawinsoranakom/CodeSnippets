async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        tool_choice: Tool | Literal["auto", "required", "none"] = "auto",
        # None means do not override the default
        # A value means to override the client default - often specified in the constructor
        json_output: Optional[bool | type[BaseModel]] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        create_args = dict(extra_create_args)
        # Convert LLMMessage objects to dictionaries with 'role' and 'content'
        # converted_messages: List[Dict[str, str | Image | list[str | Image] | list[FunctionCall]]] = []
        converted_messages: list[
            ChatCompletionRequestSystemMessage
            | ChatCompletionRequestUserMessage
            | ChatCompletionRequestAssistantMessage
            | ChatCompletionRequestUserMessage
            | ChatCompletionRequestToolMessage
            | ChatCompletionRequestFunctionMessage
        ] = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                converted_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, UserMessage) and isinstance(msg.content, str):
                converted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AssistantMessage) and isinstance(msg.content, str):
                converted_messages.append({"role": "assistant", "content": msg.content})
            elif (
                isinstance(msg, SystemMessage) or isinstance(msg, UserMessage) or isinstance(msg, AssistantMessage)
            ) and isinstance(msg.content, list):
                raise ValueError("Multi-part messages such as those containing images are currently not supported.")
            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")

        if isinstance(json_output, type) and issubclass(json_output, BaseModel):
            create_args["response_format"] = {"type": "json_object", "schema": json_output.model_json_schema()}
        elif json_output is True:
            create_args["response_format"] = {"type": "json_object"}
        elif json_output is not False and json_output is not None:
            raise ValueError("json_output must be a boolean, a BaseModel subclass or None.")

        # Handle tool_choice parameter
        if tool_choice != "auto":
            warnings.warn(
                "tool_choice parameter is specified but LlamaCppChatCompletionClient does not support it. "
                "This parameter will be ignored.",
                UserWarning,
                stacklevel=2,
            )

        if self.model_info["function_calling"]:
            # Run this in on the event loop to avoid blocking.
            response_future = asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.llm.create_chat_completion(
                    messages=converted_messages, tools=convert_tools(tools), stream=False, **create_args
                ),
            )
        else:
            response_future = asyncio.get_event_loop().run_in_executor(
                None, lambda: self.llm.create_chat_completion(messages=converted_messages, stream=False, **create_args)
            )
        if cancellation_token:
            cancellation_token.link_future(response_future)
        response = await response_future

        if not isinstance(response, dict):
            raise ValueError("Unexpected response type from LlamaCpp model.")

        self._total_usage["prompt_tokens"] += response["usage"]["prompt_tokens"]
        self._total_usage["completion_tokens"] += response["usage"]["completion_tokens"]

        # Parse the response
        response_tool_calls: ChatCompletionTool | None = None
        response_text: str | None = None
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                response_text = response["choices"][0]["message"]["content"]
            if "tool_calls" in response["choices"][0]:
                response_tool_calls = response["choices"][0]["tool_calls"]  # type: ignore

        content: List[FunctionCall] | str = ""
        thought: str | None = None
        if response_tool_calls:
            content = []
            for tool_call in response_tool_calls:
                if not isinstance(tool_call, dict):
                    raise ValueError("Unexpected tool call type from LlamaCpp model.")
                content.append(
                    FunctionCall(
                        id=tool_call["id"],
                        arguments=tool_call["function"]["arguments"],
                        name=normalize_name(tool_call["function"]["name"]),
                    )
                )
            if response_text and len(response_text) > 0:
                thought = response_text
        else:
            if response_text:
                content = response_text

        # Detect tool usage in the response
        if not response_tool_calls and not response_text:
            logger.debug("DEBUG: No response text found. Returning empty response.")
            return CreateResult(
                content="", usage=RequestUsage(prompt_tokens=0, completion_tokens=0), finish_reason="stop", cached=False
            )

        # Create a CreateResult object
        if "finish_reason" in response["choices"][0]:
            finish_reason = response["choices"][0]["finish_reason"]
        else:
            finish_reason = "unknown"
        if finish_reason not in ("stop", "length", "function_calls", "content_filter", "unknown"):
            finish_reason = "unknown"
        create_result = CreateResult(
            content=content,
            thought=thought,
            usage=cast(RequestUsage, response["usage"]),
            finish_reason=normalize_stop_reason(finish_reason),  # type: ignore
            cached=False,
        )

        # If we are running in the context of a handler we can get the agent_id
        try:
            agent_id = MessageHandlerContext.agent_id()
        except RuntimeError:
            agent_id = None

        logger.info(
            LLMCallEvent(
                messages=cast(List[Dict[str, Any]], converted_messages),
                response=create_result.model_dump(),
                prompt_tokens=response["usage"]["prompt_tokens"],
                completion_tokens=response["usage"]["completion_tokens"],
                agent_id=agent_id,
            )
        )
        return create_result