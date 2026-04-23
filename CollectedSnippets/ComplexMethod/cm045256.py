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
        # Copy create args and update with extra args
        create_args = self._create_args.copy()
        create_args.update(extra_create_args)

        # Check for vision capability if images are present
        if self.model_info["vision"] is False:
            for message in messages:
                if isinstance(message, UserMessage):
                    if isinstance(message.content, list) and any(isinstance(x, Image) for x in message.content):
                        raise ValueError("Model does not support vision and image was provided")

        # Handle JSON output format
        if json_output is not None:
            if self.model_info["json_output"] is False and json_output is True:
                raise ValueError("Model does not support JSON output")

            if json_output is True:
                create_args["response_format"] = {"type": "json_object"}
            elif isinstance(json_output, type):
                raise ValueError("Structured output is currently not supported for Anthropic models")

        # Process system message separately
        system_message = None
        anthropic_messages: List[MessageParam] = []

        # Merge continuous system messages into a single message
        messages = self._merge_system_messages(messages)
        messages = self._rstrip_last_assistant_message(messages)

        for message in messages:
            if isinstance(message, SystemMessage):
                if system_message is not None:
                    # if that case, system message is must only one
                    raise ValueError("Multiple system messages are not supported")
                system_message = to_anthropic_type(message)
            else:
                anthropic_message = to_anthropic_type(message)
                if isinstance(anthropic_message, list):
                    anthropic_messages.extend(anthropic_message)
                elif isinstance(anthropic_message, str):
                    msg = MessageParam(
                        role="user" if isinstance(message, UserMessage) else "assistant", content=anthropic_message
                    )
                    anthropic_messages.append(msg)
                else:
                    anthropic_messages.append(anthropic_message)

        # Check for function calling support
        if self.model_info["function_calling"] is False and len(tools) > 0:
            raise ValueError("Model does not support function calling")

        # Set up the request
        request_args: Dict[str, Any] = {
            "model": create_args["model"],
            "messages": anthropic_messages,
            "max_tokens": create_args.get("max_tokens", 4096),
            "temperature": create_args.get("temperature", 1.0),
        }

        # Add system message if present
        if system_message is not None:
            request_args["system"] = system_message

        has_tool_results = any(isinstance(msg, FunctionExecutionResultMessage) for msg in messages)

        # Store and add tools if present
        if len(tools) > 0:
            converted_tools = convert_tools(tools)
            self._last_used_tools = converted_tools
            request_args["tools"] = converted_tools
        elif has_tool_results:
            # anthropic requires tools to be present even if there is any tool use
            request_args["tools"] = self._last_used_tools

        # Process tool_choice parameter
        if isinstance(tool_choice, Tool):
            if len(tools) == 0 and not has_tool_results:
                raise ValueError("tool_choice specified but no tools provided")

            # Validate that the tool exists in the provided tools
            tool_names_available: List[str] = []
            if len(tools) > 0:
                for tool in tools:
                    if isinstance(tool, Tool):
                        tool_names_available.append(tool.schema["name"])
                    else:
                        tool_names_available.append(tool["name"])
            else:
                # Use last used tools names if available
                for tool_param in self._last_used_tools:
                    tool_names_available.append(tool_param["name"])

            # tool_choice is a single Tool object
            tool_name = tool_choice.schema["name"]
            if tool_name not in tool_names_available:
                raise ValueError(f"tool_choice references '{tool_name}' but it's not in the available tools")

        # Convert to Anthropic format and add to request_args only if tools are provided
        # According to Anthropic API, tool_choice may only be specified while providing tools
        if len(tools) > 0 or has_tool_results:
            converted_tool_choice = convert_tool_choice_anthropic(tool_choice)
            if converted_tool_choice is not None:
                request_args["tool_choice"] = converted_tool_choice

        # Optional parameters
        for param in ["top_p", "top_k", "stop_sequences", "metadata"]:
            if param in create_args:
                request_args[param] = create_args[param]

        # Add thinking configuration if available
        thinking_config = self._get_thinking_config(extra_create_args)
        if thinking_config:
            request_args.update(thinking_config)

        # Execute the request
        future: asyncio.Task[Message] = asyncio.ensure_future(self._client.messages.create(**request_args))  # type: ignore

        if cancellation_token is not None:
            cancellation_token.link_future(future)  # type: ignore

        result: Message = cast(Message, await future)  # type: ignore

        # Extract usage statistics
        usage = RequestUsage(
            prompt_tokens=result.usage.input_tokens,
            completion_tokens=result.usage.output_tokens,
        )
        serializable_messages: List[Dict[str, Any]] = [self._serialize_message(msg) for msg in anthropic_messages]

        logger.info(
            LLMCallEvent(
                messages=serializable_messages,
                response=result.model_dump(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        )

        # Process the response
        content: Union[str, List[FunctionCall]]
        thought = None

        # Check if the response includes tool uses
        tool_uses = [block for block in result.content if getattr(block, "type", None) == "tool_use"]

        # Check for thinking blocks
        thinking_blocks = [block for block in result.content if getattr(block, "type", None) == "thinking"]

        if tool_uses:
            # Handle tool use response
            content = []

            # Extract thinking content
            if thinking_blocks:
                thought = "".join([getattr(block, "thinking", "") for block in thinking_blocks])
            else:
                # Fallback: text content before tool calls is treated as thought
                text_blocks: List[TextBlock] = [block for block in result.content if isinstance(block, TextBlock)]
                if text_blocks:
                    thought = "".join([block.text for block in text_blocks])

            # Process tool use blocks
            for tool_use in tool_uses:
                if isinstance(tool_use, ToolUseBlock):
                    tool_input = tool_use.input
                    if isinstance(tool_input, dict):
                        tool_input = json.dumps(tool_input)
                    else:
                        tool_input = str(tool_input) if tool_input is not None else ""

                    content.append(
                        FunctionCall(
                            id=tool_use.id,
                            name=normalize_name(tool_use.name),
                            arguments=tool_input,
                        )
                    )
        else:
            # Handle text response
            if thinking_blocks:
                # Extract thinking content
                thought = "".join([getattr(block, "thinking", "") for block in thinking_blocks])
                # Get only text content for the main content field
                content = "".join([block.text if isinstance(block, TextBlock) else "" for block in result.content])
            else:
                # No thinking blocks, just get text content
                content = "".join([block.text if isinstance(block, TextBlock) else "" for block in result.content])

        # Create the final result
        response = CreateResult(
            finish_reason=normalize_stop_reason(result.stop_reason),
            content=content,
            usage=usage,
            cached=False,
            thought=thought,
        )

        # Update usage statistics
        self._total_usage = _add_usage(self._total_usage, usage)
        self._actual_usage = _add_usage(self._actual_usage, usage)

        return response