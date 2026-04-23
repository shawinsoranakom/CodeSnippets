def with_structured_output(
        self,
        schema: dict | type[BaseModel] | None = None,
        *,
        method: Literal[
            "function_calling", "json_mode", "json_schema"
        ] = "function_calling",
        include_raw: bool = False,
        strict: bool | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, dict | BaseModel]:
        r"""Model wrapper that returns outputs formatted to match the given schema.

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

                !!! warning "Behavior changed in `langchain-groq` 0.3.8"

                    Added support for Groq's dedicated structured output feature via
                    `method="json_schema"`.

            method: The method for steering model generation, one of:

                - `'function_calling'`:
                    Uses Groq's tool-calling [API](https://console.groq.com/docs/tool-use)
                - `'json_schema'`:
                    Uses Groq's [Structured Output API](https://console.groq.com/docs/structured-outputs).
                    Supported for a subset of models. See [docs](https://console.groq.com/docs/structured-outputs)
                    for details.
                - `'json_mode'`:
                    Uses Groq's [JSON mode](https://console.groq.com/docs/structured-outputs#json-object-mode).
                    Note that if using JSON mode then you must include instructions for
                    formatting the output into the desired schema into the model call

                Learn more about the differences between the methods and which models
                support which methods [here](https://console.groq.com/docs/structured-outputs).

            method:
                The method for steering model generation, either `'function_calling'`
                or `'json_mode'`. If `'function_calling'` then the schema will be converted
                to an OpenAI function and the returned model will make use of the
                function-calling API. If `'json_mode'` then JSON mode will be used.

                !!! note
                    If using `'json_mode'` then you must include instructions for formatting
                    the output into the desired schema into the model call. (either via the
                    prompt itself or in the system message/prompt/instructions).

                !!! warning
                    `'json_mode'` does not support streaming responses stop sequences.

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
                Only used with `method="json_schema"`. When `True`, Groq's Structured
                Output API uses constrained decoding to guarantee schema compliance.
                This requires every object to set `additionalProperties: false` and
                all properties to be listed in `required`. When `False`, schema
                adherence is best-effort. If `None`, the argument is omitted.

                Strict mode is only supported for `openai/gpt-oss-20b` and
                `openai/gpt-oss-120b`. For other models, `strict=True` is ignored.

            kwargs:
                Any additional parameters to pass to the `langchain.runnable.Runnable`
                constructor.

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

        Example: schema=Pydantic class, method="function_calling", include_raw=False:

        ```python
        from typing import Optional

        from langchain_groq import ChatGroq
        from pydantic import BaseModel, Field


        class AnswerWithJustification(BaseModel):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            # If we provide default values and/or descriptions for fields, these will be passed
            # to the model. This is an important part of improving a model's ability to
            # correctly return structured outputs.
            justification: str | None = Field(default=None, description="A justification for the answer.")


        model = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        structured_model = model.with_structured_output(AnswerWithJustification)

        structured_model.invoke("What weighs more a pound of bricks or a pound of feathers")

        # -> AnswerWithJustification(
        #     answer='They weigh the same',
        #     justification='Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ.'
        # )
        ```

        Example: schema=Pydantic class, method="function_calling", include_raw=True:

        ```python
        from langchain_groq import ChatGroq
        from pydantic import BaseModel


        class AnswerWithJustification(BaseModel):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            justification: str


        model = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        structured_model = model.with_structured_output(
            AnswerWithJustification,
            include_raw=True,
        )

        structured_model.invoke("What weighs more a pound of bricks or a pound of feathers")
        # -> {
        #     'raw': AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_Ao02pnFYXD6GN1yzc0uXPsvF', 'function': {'arguments': '{"answer":"They weigh the same.","justification":"Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ."}', 'name': 'AnswerWithJustification'}, 'type': 'function'}]}),
        #     'parsed': AnswerWithJustification(answer='They weigh the same.', justification='Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ.'),
        #     'parsing_error': None
        # }
        ```

        Example: schema=TypedDict class, method="function_calling", include_raw=False:

        ```python
        from typing_extensions import Annotated, TypedDict

        from langchain_groq import ChatGroq


        class AnswerWithJustification(TypedDict):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            justification: Annotated[str | None, None, "A justification for the answer."]


        model = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        structured_model = model.with_structured_output(AnswerWithJustification)

        structured_model.invoke("What weighs more a pound of bricks or a pound of feathers")
        # -> {
        #     'answer': 'They weigh the same',
        #     'justification': 'Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume and density of the two substances differ.'
        # }
        ```

        Example: schema=OpenAI function schema, method="function_calling", include_raw=False:

        ```python
        from langchain_groq import ChatGroq

        oai_schema = {
            'name': 'AnswerWithJustification',
            'description': 'An answer to the user question along with justification for the answer.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'answer': {'type': 'string'},
                    'justification': {'description': 'A justification for the answer.', 'type': 'string'}
                },
                'required': ['answer']
            }

            model = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
            structured_model = model.with_structured_output(oai_schema)

            structured_model.invoke(
                "What weighs more a pound of bricks or a pound of feathers"
            )
            # -> {
            #     'answer': 'They weigh the same',
            #     'justification': 'Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume and density of the two substances differ.'
            # }
        ```

        Example: schema=Pydantic class, method="json_schema", include_raw=False:

        ```python
        from typing import Optional

        from langchain_groq import ChatGroq
        from pydantic import BaseModel, Field


        class AnswerWithJustification(BaseModel):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            # If we provide default values and/or descriptions for fields, these will be passed
            # to the model. This is an important part of improving a model's ability to
            # correctly return structured outputs.
            justification: str | None = Field(default=None, description="A justification for the answer.")


        model = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        structured_model = model.with_structured_output(
            AnswerWithJustification,
            method="json_schema",
        )

        structured_model.invoke("What weighs more a pound of bricks or a pound of feathers")

        # -> AnswerWithJustification(
        #     answer='They weigh the same',
        #     justification='Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ.'
        # )
        ```

        Example: schema=Pydantic class, method="json_mode", include_raw=True:

        ```python
        from langchain_groq import ChatGroq
        from pydantic import BaseModel


        class AnswerWithJustification(BaseModel):
            answer: str
            justification: str


        model = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        structured_model = model.with_structured_output(
            AnswerWithJustification, method="json_mode", include_raw=True
        )

        structured_model.invoke(
            "Answer the following question. "
            "Make sure to return a JSON blob with keys 'answer' and 'justification'.\n\n"
            "What's heavier a pound of bricks or a pound of feathers?"
        )
        # -> {
        #     'raw': AIMessage(content='{\n    "answer": "They are both the same weight.",\n    "justification": "Both a pound of bricks and a pound of feathers weigh one pound. The difference lies in the volume and density of the materials, not the weight." \n}'),
        #     'parsed': AnswerWithJustification(answer='They are both the same weight.', justification='Both a pound of bricks and a pound of feathers weigh one pound. The difference lies in the volume and density of the materials, not the weight.'),
        #     'parsing_error': None
        # }
        ```

        """  # noqa: E501
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
                ls_structured_output_format={
                    "kwargs": {"method": "function_calling"},
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
            # Use structured outputs (json_schema) for models that support it
            # Convert schema to JSON Schema format for structured outputs
            if schema is None:
                msg = (
                    "schema must be specified when method is 'json_schema'. "
                    "Received None."
                )
                raise ValueError(msg)
            if (
                strict is True
                and self.model_name not in _STRICT_STRUCTURED_OUTPUT_MODELS
            ):
                # Ignore unsupported strict=True to preserve backward compatibility.
                strict = None
            json_schema = convert_to_json_schema(schema, strict=strict)
            schema_name = json_schema.get("title", "")
            response_format: dict[str, Any] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": json_schema},
            }
            if strict is not None:
                response_format["json_schema"]["strict"] = strict
            ls_format_kwargs: dict[str, Any] = {"method": "json_schema"}
            if strict is not None:
                ls_format_kwargs["strict"] = strict
            ls_format_info = {
                "kwargs": ls_format_kwargs,
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

        elif method == "json_mode":
            llm = self.bind(
                response_format={"type": "json_object"},
                ls_structured_output_format={
                    "kwargs": {"method": "json_mode"},
                    "schema": schema,
                },
                **kwargs,
            )
            output_parser = (
                PydanticOutputParser(pydantic_object=schema)  # type: ignore[type-var, arg-type]
                if is_pydantic_schema
                else JsonOutputParser()
            )
        else:
            msg = (
                "Unrecognized method argument. Expected one of "
                "'function_calling', 'json_mode', or 'json_schema'. "
                f"Received: '{method}'"
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