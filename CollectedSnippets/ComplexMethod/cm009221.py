def with_structured_output(
        self,
        schema: dict | type,
        *,
        include_raw: bool = False,
        method: Literal["function_calling", "json_schema"] = "function_calling",
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, dict | BaseModel]:
        """Model wrapper that returns outputs formatted to match the given schema.

        See the [LangChain docs](https://docs.langchain.com/oss/python/integrations/chat/anthropic#structured-output)
        for more details and examples.

        Args:
            schema: The output schema. Can be passed in as:

                - An Anthropic tool schema,
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
            include_raw:
                If `False` then only the parsed structured output is returned.

                If an error occurs during model output parsing it will be raised.

                If `True` then both the raw model response (a `BaseMessage`) and the
                parsed model response will be returned.

                If an error occurs during output parsing it will be caught and returned
                as well.

                The final output is always a `dict` with keys `'raw'`, `'parsed'`, and
                `'parsing_error'`.
            method: The structured output method to use. Options are:

                - `'function_calling'` (default): Use forced tool calling to get
                    structured output.
                - `'json_schema'`: Use Claude's dedicated
                    [structured output](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
                    feature.

            kwargs: Additional keyword arguments are ignored.

        Returns:
            A `Runnable` that takes same inputs as a
                `langchain_core.language_models.chat.BaseChatModel`.

                If `include_raw` is `False` and `schema` is a Pydantic class, `Runnable`
                outputs an instance of `schema` (i.e., a Pydantic object). Otherwise, if
                `include_raw` is `False` then `Runnable` outputs a `dict`.

                If `include_raw` is `True`, then `Runnable` outputs a `dict` with keys:

                - `'raw'`: `BaseMessage`
                - `'parsed'`: `None` if there was a parsing error, otherwise the type
                    depends on the `schema` as described above.
                - `'parsing_error'`: `BaseException | None`

        Example:
            ```python hl_lines="13"
            from langchain_anthropic import ChatAnthropic
            from pydantic import BaseModel, Field

            model = ChatAnthropic(model="claude-sonnet-4-5")

            class Movie(BaseModel):
                \"\"\"A movie with details.\"\"\"
                title: str = Field(..., description="The title of the movie")
                year: int = Field(..., description="The year the movie was released")
                director: str = Field(..., description="The director of the movie")
                rating: float = Field(..., description="The movie's rating out of 10")

            model_with_structure = model.with_structured_output(Movie, method="json_schema")
            response = model_with_structure.invoke("Provide details about the movie Inception")
            print(response)
            # -> Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
            ```
        """  # noqa: E501
        if method == "json_mode":
            warning_message = (
                "Unrecognized structured output method 'json_mode'. Defaulting to "
                "'json_schema' method."
            )
            warnings.warn(warning_message, stacklevel=2)
            method = "json_schema"

        if method == "function_calling":
            formatted_tool = cast(AnthropicTool, convert_to_anthropic_tool(schema))
            # The result of convert_to_anthropic_tool for 'method=function_calling' will
            # always be an AnthropicTool
            tool_name = formatted_tool["name"]
            if self.thinking is not None and self.thinking.get("type") in (
                "enabled",
                "adaptive",
            ):
                llm = self._get_llm_for_structured_output_when_thinking_is_enabled(
                    schema,
                    formatted_tool,
                )
            else:
                llm = self.bind_tools(
                    [schema],
                    tool_choice=tool_name,  # Force tool call
                    ls_structured_output_format={
                        "kwargs": {"method": "function_calling"},
                        "schema": formatted_tool,
                    },
                )

            if isinstance(schema, type) and is_basemodel_subclass(schema):
                output_parser: OutputParserLike = PydanticToolsParser(
                    tools=[schema],
                    first_tool_only=True,
                )
            else:
                output_parser = JsonOutputKeyToolsParser(
                    key_name=tool_name,
                    first_tool_only=True,
                )
        elif method == "json_schema":
            llm = self.bind(
                output_config={
                    "format": _convert_to_anthropic_output_config_format(schema)
                },
                ls_structured_output_format={
                    "kwargs": {"method": "json_schema"},
                    "schema": convert_to_openai_tool(schema),
                },
            )
            if isinstance(schema, type) and is_basemodel_subclass(schema):
                output_parser = PydanticOutputParser(pydantic_object=schema)
            else:
                output_parser = JsonOutputParser()
        else:
            error_message = (
                f"Unrecognized structured output method '{method}'. "
                f"Expected 'function_calling' or 'json_schema'."
            )
            raise ValueError(error_message)

        if include_raw:
            parser_assign = RunnablePassthrough.assign(
                parsed=itemgetter("raw") | output_parser,
                parsing_error=lambda _: None,
            )
            parser_none = RunnablePassthrough.assign(parsed=lambda _: None)
            parser_with_fallback = parser_assign.with_fallbacks(
                [parser_none],
                exception_key="parsing_error",
            )
            return RunnableMap(raw=llm) | parser_with_fallback
        return llm | output_parser