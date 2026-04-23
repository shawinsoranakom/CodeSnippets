def _process_create_args(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema],
        tool_choice: Tool | Literal["auto", "required", "none"],
        json_output: Optional[bool | type[BaseModel]],
        extra_create_args: Mapping[str, Any],
    ) -> CreateParams:
        # Copy the create args and overwrite anything in extra_create_args
        create_args = self._create_args.copy()
        create_args.update(extra_create_args)
        create_args = _create_args_from_config(create_args)

        response_format_value: JsonSchemaValue | Literal["json"] | None = None

        if "response_format" in create_args:
            warnings.warn(
                "Using response_format will be deprecated. Use json_output instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            value = create_args["response_format"]
            if isinstance(value, type) and issubclass(value, BaseModel):
                response_format_value = value.model_json_schema()
                # Remove response_format from create_args to prevent passing it twice.
                del create_args["response_format"]
            else:
                raise ValueError(f"response_format must be a Pydantic model class, not {type(value)}")

        if json_output is not None:
            if self.model_info["json_output"] is False and json_output is True:
                raise ValueError("Model does not support JSON output.")
            if json_output is True:
                # JSON mode.
                response_format_value = "json"
            elif json_output is False:
                # Text mode.
                response_format_value = None
            elif isinstance(json_output, type) and issubclass(json_output, BaseModel):
                if response_format_value is not None:
                    raise ValueError(
                        "response_format and json_output cannot be set to a Pydantic model class at the same time. "
                        "Use json_output instead."
                    )
                # Beta client mode with Pydantic model class.
                response_format_value = json_output.model_json_schema()
            else:
                raise ValueError(f"json_output must be a boolean or a Pydantic model class, got {type(json_output)}")

        if "format" in create_args:
            # Handle the case where format is set from create_args.
            if json_output is not None:
                raise ValueError("json_output and format cannot be set at the same time. Use json_output instead.")
            assert response_format_value is None
            response_format_value = create_args["format"]
            # Remove format from create_args to prevent passing it twice.
            del create_args["format"]

        # TODO: allow custom handling.
        # For now we raise an error if images are present and vision is not supported
        if self.model_info["vision"] is False:
            for message in messages:
                if isinstance(message, UserMessage):
                    if isinstance(message.content, list) and any(isinstance(x, Image) for x in message.content):
                        raise ValueError("Model does not support vision and image was provided")

        if self.model_info["json_output"] is False and json_output is True:
            raise ValueError("Model does not support JSON output.")

        ollama_messages_nested = [to_ollama_type(m) for m in messages]
        ollama_messages = [item for sublist in ollama_messages_nested for item in sublist]

        if self.model_info["function_calling"] is False and len(tools) > 0:
            raise ValueError("Model does not support function calling and tools were provided")

        converted_tools: List[OllamaTool] = []

        # Handle tool_choice parameter in a way that is compatible with Ollama API.
        if isinstance(tool_choice, Tool):
            # If tool_choice is a Tool, convert it to OllamaTool.
            converted_tools = convert_tools([tool_choice])
        elif tool_choice == "none":
            # No tool choice, do not pass tools to the API.
            converted_tools = []
        elif tool_choice == "required":
            # Required tool choice, pass tools to the API.
            converted_tools = convert_tools(tools)
            if len(converted_tools) == 0:
                raise ValueError("tool_choice 'required' specified but no tools provided")
        else:
            converted_tools = convert_tools(tools)

        return CreateParams(
            messages=ollama_messages,
            tools=converted_tools,
            format=response_format_value,
            create_args=create_args,
        )