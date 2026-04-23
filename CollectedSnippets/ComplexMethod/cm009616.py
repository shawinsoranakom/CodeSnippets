def _parse_input(
        self, tool_input: str | dict, tool_call_id: str | None
    ) -> str | dict[str, Any]:
        """Parse and validate tool input using the args schema.

        Args:
            tool_input: The raw input to the tool.
            tool_call_id: The ID of the tool call, if available.

        Returns:
            The parsed and validated input.

        Raises:
            ValueError: If `string` input is provided with JSON schema `args_schema`.
            ValueError: If `InjectedToolCallId` is required but `tool_call_id` is not
                provided.
            TypeError: If `args_schema` is not a Pydantic `BaseModel` or dict.
        """
        input_args = self.args_schema

        if isinstance(tool_input, str):
            if input_args is not None:
                if isinstance(input_args, dict):
                    msg = (
                        "String tool inputs are not allowed when "
                        "using tools with JSON schema args_schema."
                    )
                    raise ValueError(msg)
                key_ = next(iter(get_fields(input_args).keys()))
                if issubclass(input_args, BaseModel):
                    input_args.model_validate({key_: tool_input})
                elif issubclass(input_args, BaseModelV1):
                    input_args.parse_obj({key_: tool_input})
                else:
                    msg = f"args_schema must be a Pydantic BaseModel, got {input_args}"
                    raise TypeError(msg)
            return tool_input

        if input_args is not None:
            if isinstance(input_args, dict):
                return tool_input
            if issubclass(input_args, BaseModel):
                # Check args_schema for InjectedToolCallId
                for k, v in get_all_basemodel_annotations(input_args).items():
                    if _is_injected_arg_type(v, injected_type=InjectedToolCallId):
                        if tool_call_id is None:
                            msg = (
                                "When tool includes an InjectedToolCallId "
                                "argument, tool must always be invoked with a full "
                                "model ToolCall of the form: {'args': {...}, "
                                "'name': '...', 'type': 'tool_call', "
                                "'tool_call_id': '...'}"
                            )
                            raise ValueError(msg)
                        tool_input[k] = tool_call_id
                result = input_args.model_validate(tool_input)
                result_dict = result.model_dump()
            elif issubclass(input_args, BaseModelV1):
                # Check args_schema for InjectedToolCallId
                for k, v in get_all_basemodel_annotations(input_args).items():
                    if _is_injected_arg_type(v, injected_type=InjectedToolCallId):
                        if tool_call_id is None:
                            msg = (
                                "When tool includes an InjectedToolCallId "
                                "argument, tool must always be invoked with a full "
                                "model ToolCall of the form: {'args': {...}, "
                                "'name': '...', 'type': 'tool_call', "
                                "'tool_call_id': '...'}"
                            )
                            raise ValueError(msg)
                        tool_input[k] = tool_call_id
                result = input_args.parse_obj(tool_input)
                result_dict = result.dict()
            else:
                msg = (
                    f"args_schema must be a Pydantic BaseModel, got {self.args_schema}"
                )
                raise NotImplementedError(msg)

            # Include fields from tool_input, plus fields with explicit defaults.
            # This applies Pydantic defaults (like Field(default=1)) while excluding
            # synthetic "args"/"kwargs" fields that Pydantic creates for *args/**kwargs.
            field_info = get_fields(input_args)
            validated_input = {}
            for k in result_dict:
                if k in tool_input:
                    # Field was provided in input - include it (validated)
                    validated_input[k] = getattr(result, k)
                elif k in field_info and k not in {"args", "kwargs"}:
                    # Check if field has an explicit default defined in the schema.
                    # Exclude "args"/"kwargs" as these are synthetic fields for variadic
                    # parameters that should not be passed as keyword arguments.
                    fi = field_info[k]
                    # Pydantic v2 uses is_required() method, v1 uses required attribute
                    has_default = (
                        not fi.is_required()
                        if hasattr(fi, "is_required")
                        else not getattr(fi, "required", True)
                    )
                    if has_default:
                        validated_input[k] = getattr(result, k)

            for k in self._injected_args_keys:
                if k in tool_input:
                    validated_input[k] = tool_input[k]
                elif k == "tool_call_id":
                    if tool_call_id is None:
                        msg = (
                            "When tool includes an InjectedToolCallId "
                            "argument, tool must always be invoked with a full "
                            "model ToolCall of the form: {'args': {...}, "
                            "'name': '...', 'type': 'tool_call', "
                            "'tool_call_id': '...'}"
                        )
                        raise ValueError(msg)
                    validated_input[k] = tool_call_id

            return validated_input

        return tool_input