def with_structured_output(  # type: ignore[override]
        self,
        schema: dict | type[BaseModel] | None = None,
        *,
        method: Literal["function_calling", "json_schema"] = "function_calling",
        include_raw: bool = False,
        strict: bool | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, dict | BaseModel]:
        """Model wrapper that returns outputs formatted to match the given schema.

        Args:
            schema: The output schema as a Pydantic class, TypedDict, JSON Schema,
                or OpenAI function schema.
            method: The method for steering model generation.
            include_raw: If `True` then both the raw model response and the
                parsed model response will be returned.
            strict: If `True`, model output is guaranteed to exactly match the
                JSON Schema provided in the schema definition.

                If `None`, the `strict` argument will not be passed to
                the model.
            **kwargs: Any additional parameters.

        Returns:
            A `Runnable` that takes same inputs as a `BaseChatModel`.
        """
        if method == "json_mode":
            warnings.warn(
                "Unrecognized structured output method 'json_mode'. "
                "Defaulting to 'json_schema' method.",
                stacklevel=2,
            )
            method = "json_schema"
        is_pydantic_schema = _is_pydantic_class(schema)
        if method == "function_calling":
            if schema is None:
                msg = (
                    "schema must be specified when method is 'function_calling'. "
                    "Received None."
                )
                raise ValueError(msg)
            formatted_tool = convert_to_openai_tool(schema)
            tool_name = formatted_tool["function"]["name"]
            llm = self.bind_tools(
                [schema],
                tool_choice=tool_name,
                strict=strict,
                ls_structured_output_format={
                    "kwargs": {"method": "function_calling", "strict": strict},
                    "schema": formatted_tool,
                },
                **kwargs,
            )
            if is_pydantic_schema:
                output_parser: OutputParserLike = PydanticToolsParser(
                    tools=[schema],  # type: ignore[list-item]
                    first_tool_only=True,  # type: ignore[list-item]
                )
            else:
                output_parser = JsonOutputKeyToolsParser(
                    key_name=tool_name, first_tool_only=True
                )
        elif method == "json_schema":
            if schema is None:
                msg = (
                    "schema must be specified when method is 'json_schema'. "
                    "Received None."
                )
                raise ValueError(msg)
            json_schema = convert_to_json_schema(schema)
            schema_name = json_schema.get("title", "")
            json_schema_spec: dict[str, Any] = {
                "name": schema_name,
                "schema": json_schema,
            }
            if strict is not None:
                json_schema_spec["strict"] = strict
            response_format = {
                "type": "json_schema",
                "json_schema": json_schema_spec,
            }
            ls_format_info = {
                "kwargs": {"method": "json_schema", "strict": strict},
                "schema": json_schema,
            }
            llm = self.bind(
                response_format=response_format,
                ls_structured_output_format=ls_format_info,
                **kwargs,
            )
            output_parser = (
                PydanticOutputParser(pydantic_object=schema)  # type: ignore[type-var, arg-type]
                if is_pydantic_schema
                else JsonOutputParser()
            )
        else:
            msg = (
                f"Unrecognized method argument. Expected one of 'function_calling' "
                f"or 'json_schema'. Received: '{method}'"
            )
            raise ValueError(msg)

        if include_raw:
            parser_assign = RunnablePassthrough.assign(
                parsed=itemgetter("raw") | output_parser, parsing_error=lambda _: None
            )
            parser_none = RunnablePassthrough.assign(parsed=lambda _: None)
            parser_with_fallback = parser_assign.with_fallbacks(
                [parser_none], exception_key="parsing_error"
            )
            return RunnableMap(raw=llm) | parser_with_fallback
        return llm | output_parser