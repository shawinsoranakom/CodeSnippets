def _process_create_args(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema],
        tool_choice: Tool | Literal["auto", "required", "none"],
        json_output: Optional[bool | type[BaseModel]],
        extra_create_args: Mapping[str, Any],
    ) -> CreateParams:
        # Make sure all extra_create_args are valid
        extra_create_args_keys = set(extra_create_args.keys())
        if not create_kwargs.issuperset(extra_create_args_keys):
            raise ValueError(f"Extra create args are invalid: {extra_create_args_keys - create_kwargs}")

        # Copy the create args and overwrite anything in extra_create_args
        create_args = self._create_args.copy()
        create_args.update(extra_create_args)

        # The response format value to use for the beta client.
        response_format_value: Optional[Type[BaseModel]] = None

        if "response_format" in create_args:
            # Legacy support for getting beta client mode from response_format.
            value = create_args["response_format"]
            if isinstance(value, type) and issubclass(value, BaseModel):
                if self.model_info["structured_output"] is False:
                    raise ValueError("Model does not support structured output.")
                warnings.warn(
                    "Using response_format to specify the BaseModel for structured output type will be deprecated. "
                    "Use json_output in create and create_stream instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                response_format_value = value
                # Remove response_format from create_args to prevent passing it twice.
                del create_args["response_format"]
            # In all other cases when response_format is set to something else, we will
            # use the regular client.

        if json_output is not None:
            if self.model_info["json_output"] is False and json_output is True:
                raise ValueError("Model does not support JSON output.")
            if json_output is True:
                # JSON mode.
                create_args["response_format"] = ResponseFormatJSONObject(type="json_object")
            elif json_output is False:
                # Text mode.
                create_args["response_format"] = ResponseFormatText(type="text")
            elif isinstance(json_output, type) and issubclass(json_output, BaseModel):
                if self.model_info["structured_output"] is False:
                    raise ValueError("Model does not support structured output.")
                if response_format_value is not None:
                    raise ValueError(
                        "response_format and json_output cannot be set to a Pydantic model class at the same time."
                    )
                # Beta client mode with Pydantic model class.
                response_format_value = json_output
            else:
                raise ValueError(f"json_output must be a boolean or a Pydantic model class, got {type(json_output)}")

        if response_format_value is not None and "response_format" in create_args:
            warnings.warn(
                "response_format is found in extra_create_args while json_output is set to a Pydantic model class. "
                "Skipping the response_format in extra_create_args in favor of the json_output. "
                "Structured output will be used.",
                UserWarning,
                stacklevel=2,
            )
            # If using beta client, remove response_format from create_args to prevent passing it twice
            del create_args["response_format"]

        # TODO: allow custom handling.
        # For now we raise an error if images are present and vision is not supported
        if self.model_info["vision"] is False:
            for message in messages:
                if isinstance(message, UserMessage):
                    if isinstance(message.content, list) and any(isinstance(x, Image) for x in message.content):
                        raise ValueError("Model does not support vision and image was provided")

        if self.model_info["json_output"] is False and json_output is True:
            raise ValueError("Model does not support JSON output.")

        if not self.model_info.get("multiple_system_messages", False):
            # Some models accept only one system message(or, it will read only the last one)
            # So, merge system messages into one (if multiple and continuous)
            system_message_content = ""
            _messages: List[LLMMessage] = []
            _first_system_message_idx = -1
            _last_system_message_idx = -1
            # Index of the first system message for adding the merged system message at the correct position
            for idx, message in enumerate(messages):
                if isinstance(message, SystemMessage):
                    if _first_system_message_idx == -1:
                        _first_system_message_idx = idx
                    elif _last_system_message_idx + 1 != idx:
                        # That case, system message is not continuous
                        # Merge system messages only contiues system messages
                        raise ValueError(
                            "Multiple and Not continuous system messages are not supported if model_info['multiple_system_messages'] is False"
                        )
                    system_message_content += message.content + "\n"
                    _last_system_message_idx = idx
                else:
                    _messages.append(message)
            system_message_content = system_message_content.rstrip()
            if system_message_content != "":
                system_message = SystemMessage(content=system_message_content)
                _messages.insert(_first_system_message_idx, system_message)
            messages = _messages

        # in that case, for ad-hoc, we using startswith instead of model_family for code consistency
        if create_args.get("model", "unknown").startswith("claude-"):
            # When Claude models last message is AssistantMessage, It could not end with whitespace
            messages = self._rstrip_last_assistant_message(messages)

        oai_messages_nested = [
            to_oai_type(
                m,
                prepend_name=self._add_name_prefixes,
                model=create_args.get("model", "unknown"),
                model_family=self._model_info["family"],
                include_name_in_message=self._include_name_in_message,
            )
            for m in messages
        ]

        oai_messages = [item for sublist in oai_messages_nested for item in sublist]

        if self.model_info["function_calling"] is False and len(tools) > 0:
            raise ValueError("Model does not support function calling")

        converted_tools = convert_tools(tools)

        # Process tool_choice parameter
        if isinstance(tool_choice, Tool):
            if len(tools) == 0:
                raise ValueError("tool_choice specified but no tools provided")

            # Validate that the tool exists in the provided tools
            tool_names_available: List[str] = []
            for tool in tools:
                if isinstance(tool, Tool):
                    tool_names_available.append(tool.schema["name"])
                else:
                    tool_names_available.append(tool["name"])

            # tool_choice is a single Tool object
            tool_name = tool_choice.schema["name"]
            if tool_name not in tool_names_available:
                raise ValueError(f"tool_choice references '{tool_name}' but it's not in the provided tools")

        if len(converted_tools) > 0:
            # Convert to OpenAI format and add to create_args
            converted_tool_choice = convert_tool_choice(tool_choice)
            create_args["tool_choice"] = converted_tool_choice

        return CreateParams(
            messages=oai_messages,
            tools=converted_tools,
            response_format=response_format_value,
            create_args=create_args,
        )