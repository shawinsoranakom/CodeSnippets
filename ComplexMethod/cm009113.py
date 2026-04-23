def with_structured_output(
        self,
        schema: _DictOrPydanticClass | None = None,
        *,
        method: Literal[
            "function_calling", "json_mode", "json_schema"
        ] = "function_calling",
        include_raw: bool = False,
        strict: bool | None = None,
        tools: list | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, _DictOrPydantic]:
        """Model wrapper that returns outputs formatted to match the given schema.

        Args:
            schema: The output schema. Can be passed in as:

                - An OpenAI function/tool schema,
                - A JSON Schema,
                - A `TypedDict` class,
                - Or a Pydantic class.

                If `schema` is a Pydantic class then the model output will be a
                Pydantic instance of that class, and the model-generated fields will be
                validated by the Pydantic class. Otherwise the model output will be a
                dict and will not be validated.

                See `langchain_core.utils.function_calling.convert_to_openai_tool` for
                more on how to properly specify types and descriptions of schema fields
                when specifying a Pydantic or `TypedDict` class.

            method: The method for steering model generation, one of:

                - `'function_calling'`:
                    Uses OpenAI's [tool-calling API](https://platform.openai.com/docs/guides/function-calling)
                    (formerly called function calling)
                - `'json_schema'`:
                    Uses OpenAI's [Structured Output API](https://platform.openai.com/docs/guides/structured-outputs)
                - `'json_mode'`:
                    Uses OpenAI's [JSON mode](https://platform.openai.com/docs/guides/structured-outputs/json-mode).
                    Note that if using JSON mode then you must include instructions for
                    formatting the output into the desired schema into the model call

            include_raw:
                If `False` then only the parsed structured output is returned.

                If an error occurs during model output parsing it will be raised.

                If `True` then both the raw model response (a `BaseMessage`) and the
                parsed model response will be returned.

                If an error occurs during output parsing it will be caught and returned
                as well.

                The final output is always a `dict` with keys `'raw'`, `'parsed'`, and
                `'parsing_error'`.
            strict:

                - `True`:
                    Model output is guaranteed to exactly match the schema.
                    The input schema will also be validated according to the
                    [supported schemas](https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?api-mode=responses#supported-schemas).
                - `False`:
                    Input schema will not be validated and model output will not be
                    validated.
                - `None`:
                    `strict` argument will not be passed to the model.

            tools:
                A list of tool-like objects to bind to the chat model. Requires that:

                - `method` is `'json_schema'` (default).
                - `strict=True`
                - `include_raw=True`

                If a model elects to call a tool, the resulting `AIMessage` in `'raw'`
                will include tool calls.

                ??? example

                    ```python
                    from langchain.chat_models import init_chat_model
                    from pydantic import BaseModel


                    class ResponseSchema(BaseModel):
                        response: str


                    def get_weather(location: str) -> str:
                        \"\"\"Get weather at a location.\"\"\"
                        pass

                    model = init_chat_model("openai:gpt-4o-mini")

                    structured_model = model.with_structured_output(
                        ResponseSchema,
                        tools=[get_weather],
                        strict=True,
                        include_raw=True,
                    )

                    structured_model.invoke("What's the weather in Boston?")
                    ```

                    ```python
                    {
                        "raw": AIMessage(content="", tool_calls=[...], ...),
                        "parsing_error": None,
                        "parsed": None,
                    }
                    ```

            kwargs: Additional keyword args are passed through to the model.

        Returns:
            A `Runnable` that takes same inputs as a
                `langchain_core.language_models.chat.BaseChatModel`. If `include_raw` is
                `False` and `schema` is a Pydantic class, `Runnable` outputs an instance
                of `schema` (i.e., a Pydantic object). Otherwise, if `include_raw` is
                `False` then `Runnable` outputs a `dict`.

                If `include_raw` is `True`, then `Runnable` outputs a `dict` with keys:

                - `'raw'`: `BaseMessage`
                - `'parsed'`: `None` if there was a parsing error, otherwise the type
                    depends on the `schema` as described above.
                - `'parsing_error'`: `BaseException | None`

        !!! warning "Behavior changed in `langchain-openai` 0.3.12"

            Support for `tools` added.

        !!! warning "Behavior changed in `langchain-openai` 0.3.21"

            Pass `kwargs` through to the model.
        """
        if strict is not None and method == "json_mode":
            msg = "Argument `strict` is not supported with `method`='json_mode'"
            raise ValueError(msg)
        is_pydantic_schema = _is_pydantic_class(schema)

        if method == "json_schema":
            # Check for Pydantic BaseModel V1
            if (
                is_pydantic_schema and issubclass(schema, BaseModelV1)  # type: ignore[arg-type]
            ):
                warnings.warn(
                    "Received a Pydantic BaseModel V1 schema. This is not supported by "
                    'method="json_schema". Please use method="function_calling" '
                    "or specify schema via JSON Schema or Pydantic V2 BaseModel. "
                    'Overriding to method="function_calling".'
                )
                method = "function_calling"
            # Check for incompatible model
            if self.model_name and (
                self.model_name.startswith("gpt-3")
                or self.model_name.startswith("gpt-4-")
                or self.model_name == "gpt-4"
            ):
                warnings.warn(
                    f"Cannot use method='json_schema' with model {self.model_name} "
                    f"since it doesn't support OpenAI's Structured Output API. You can "
                    f"see supported models here: "
                    f"https://platform.openai.com/docs/guides/structured-outputs#supported-models. "  # noqa: E501
                    "To fix this warning, set `method='function_calling'. "
                    "Overriding to method='function_calling'."
                )
                method = "function_calling"

        if method == "function_calling":
            if schema is None:
                msg = (
                    "schema must be specified when method is not 'json_mode'. "
                    "Received None."
                )
                raise ValueError(msg)
            tool_name = convert_to_openai_tool(schema)["function"]["name"]
            bind_kwargs = self._filter_disabled_params(
                **{
                    "tool_choice": tool_name,
                    "parallel_tool_calls": False,
                    "strict": strict,
                    "ls_structured_output_format": {
                        "kwargs": {"method": method, "strict": strict},
                        "schema": schema,
                    },
                    **kwargs,
                }
            )

            llm = self.bind_tools([schema], **bind_kwargs)
            if is_pydantic_schema:
                output_parser: Runnable = PydanticToolsParser(
                    tools=[schema],  # type: ignore[list-item]
                    first_tool_only=True,  # type: ignore[list-item]
                )
            else:
                output_parser = JsonOutputKeyToolsParser(
                    key_name=tool_name, first_tool_only=True
                )
        elif method == "json_mode":
            llm = self.bind(
                **{
                    "response_format": {"type": "json_object"},
                    "ls_structured_output_format": {
                        "kwargs": {"method": method},
                        "schema": schema,
                    },
                    **kwargs,
                }
            )
            output_parser = (
                PydanticOutputParser(pydantic_object=schema)  # type: ignore[arg-type]
                if is_pydantic_schema
                else JsonOutputParser()
            )
        elif method == "json_schema":
            if schema is None:
                msg = (
                    "schema must be specified when method is not 'json_mode'. "
                    "Received None."
                )
                raise ValueError(msg)
            response_format = _convert_to_openai_response_format(schema, strict=strict)
            bind_kwargs = {
                **dict(
                    response_format=response_format,
                    ls_structured_output_format={
                        "kwargs": {"method": method, "strict": strict},
                        "schema": convert_to_openai_tool(schema),
                    },
                    **kwargs,
                )
            }
            if tools:
                bind_kwargs["tools"] = [
                    convert_to_openai_tool(t, strict=strict) for t in tools
                ]
            llm = self.bind(**bind_kwargs)
            if is_pydantic_schema:
                output_parser = RunnableLambda(
                    partial(_oai_structured_outputs_parser, schema=cast(type, schema))
                ).with_types(output_type=cast(type, schema))
            else:
                output_parser = JsonOutputParser()
        else:
            msg = (
                f"Unrecognized method argument. Expected one of 'function_calling' or "
                f"'json_mode'. Received: '{method}'"
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