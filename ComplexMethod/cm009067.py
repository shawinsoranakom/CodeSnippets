def with_structured_output(
        self,
        schema: dict | type | None = None,
        *,
        method: Literal[
            "function_calling", "json_mode", "json_schema"
        ] = "function_calling",
        include_raw: bool = False,
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

            method: The method for steering model generation, one of:

                - `'function_calling'`:
                    Uses Mistral's
                    [function-calling feature](https://docs.mistral.ai/capabilities/function_calling/).
                - `'json_schema'`:
                    Uses Mistral's
                    [structured output feature](https://docs.mistral.ai/capabilities/structured-output/custom_structured_output/).
                - `'json_mode'`:
                    Uses Mistral's
                    [JSON mode](https://docs.mistral.ai/capabilities/structured-output/json_mode/).
                    Note that if using JSON mode then you
                    must include instructions for formatting the output into the
                    desired schema into the model call.

                !!! warning "Behavior changed in `langchain-mistralai` 0.2.5"

                    Added method="json_schema"

            include_raw:
                If `False` then only the parsed structured output is returned.

                If an error occurs during model output parsing it will be raised.

                If `True` then both the raw model response (a `BaseMessage`) and the
                parsed model response will be returned.

                If an error occurs during output parsing it will be caught and returned
                as well.

                The final output is always a `dict` with keys `'raw'`, `'parsed'`, and
                `'parsing_error'`.

            kwargs: Any additional parameters are passed directly to
                `self.bind(**kwargs)`. This is useful for passing in
                parameters such as `tool_choice` or `tools` to control
                which tool the model should call, or to pass in parameters such as
                `stop` to control when the model should stop generating output.

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

        from langchain_mistralai import ChatMistralAI
        from pydantic import BaseModel, Field


        class AnswerWithJustification(BaseModel):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            # If we provide default values and/or descriptions for fields, these will be passed
            # to the model. This is an important part of improving a model's ability to
            # correctly return structured outputs.
            justification: str | None = Field(
                default=None, description="A justification for the answer."
            )


        model = ChatMistralAI(model="mistral-large-latest", temperature=0)
        structured_model = model.with_structured_output(AnswerWithJustification)

        structured_model.invoke(
            "What weighs more a pound of bricks or a pound of feathers"
        )

        # -> AnswerWithJustification(
        #     answer='They weigh the same',
        #     justification='Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ.'
        # )
        ```

        Example: schema=Pydantic class, method="function_calling", include_raw=True:

        ```python
        from langchain_mistralai import ChatMistralAI
        from pydantic import BaseModel


        class AnswerWithJustification(BaseModel):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            justification: str


        model = ChatMistralAI(model="mistral-large-latest", temperature=0)
        structured_model = model.with_structured_output(
            AnswerWithJustification, include_raw=True
        )

        structured_model.invoke(
            "What weighs more a pound of bricks or a pound of feathers"
        )
        # -> {
        #     'raw': AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_Ao02pnFYXD6GN1yzc0uXPsvF', 'function': {'arguments': '{"answer":"They weigh the same.","justification":"Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ."}', 'name': 'AnswerWithJustification'}, 'type': 'function'}]}),
        #     'parsed': AnswerWithJustification(answer='They weigh the same.', justification='Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ.'),
        #     'parsing_error': None
        # }
        ```

        Example: schema=TypedDict class, method="function_calling", include_raw=False:

        ```python
        from typing_extensions import Annotated, TypedDict

        from langchain_mistralai import ChatMistralAI


        class AnswerWithJustification(TypedDict):
            '''An answer to the user question along with justification for the answer.'''

            answer: str
            justification: Annotated[
                str | None, None, "A justification for the answer."
            ]


        model = ChatMistralAI(model="mistral-large-latest", temperature=0)
        structured_model = model.with_structured_output(AnswerWithJustification)

        structured_model.invoke(
            "What weighs more a pound of bricks or a pound of feathers"
        )
        # -> {
        #     'answer': 'They weigh the same',
        #     'justification': 'Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume and density of the two substances differ.'
        # }
        ```

        Example: schema=OpenAI function schema, method="function_calling", include_raw=False:

        ```python
        from langchain_mistralai import ChatMistralAI

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

            model = ChatMistralAI(model="mistral-large-latest", temperature=0)
            structured_model = model.with_structured_output(oai_schema)

            structured_model.invoke(
                "What weighs more a pound of bricks or a pound of feathers"
            )
            # -> {
            #     'answer': 'They weigh the same',
            #     'justification': 'Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume and density of the two substances differ.'
            # }
        ```

        Example: schema=Pydantic class, method="json_mode", include_raw=True:

        ```python
        from langchain_mistralai import ChatMistralAI
        from pydantic import BaseModel


        class AnswerWithJustification(BaseModel):
            answer: str
            justification: str


        model = ChatMistralAI(model="mistral-large-latest", temperature=0)
        structured_model = model.with_structured_output(
            AnswerWithJustification, method="json_mode", include_raw=True
        )

        structured_model.invoke(
            "Answer the following question. "
            "Make sure to return a JSON blob with keys 'answer' and 'justification'.\\n\\n"
            "What's heavier a pound of bricks or a pound of feathers?"
        )
        # -> {
        #     'raw': AIMessage(content='{\\n    "answer": "They are both the same weight.",\\n    "justification": "Both a pound of bricks and a pound of feathers weigh one pound. The difference lies in the volume and density of the materials, not the weight." \\n}'),
        #     'parsed': AnswerWithJustification(answer='They are both the same weight.', justification='Both a pound of bricks and a pound of feathers weigh one pound. The difference lies in the volume and density of the materials, not the weight.'),
        #     'parsing_error': None
        # }
        ```

        Example: schema=None, method="json_mode", include_raw=True:

        ```python
        structured_model = model.with_structured_output(
            method="json_mode", include_raw=True
        )

        structured_model.invoke(
            "Answer the following question. "
            "Make sure to return a JSON blob with keys 'answer' and 'justification'.\\n\\n"
            "What's heavier a pound of bricks or a pound of feathers?"
        )
        # -> {
        #     'raw': AIMessage(content='{\\n    "answer": "They are both the same weight.",\\n    "justification": "Both a pound of bricks and a pound of feathers weigh one pound. The difference lies in the volume and density of the materials, not the weight." \\n}'),
        #     'parsed': {
        #         'answer': 'They are both the same weight.',
        #         'justification': 'Both a pound of bricks and a pound of feathers weigh one pound. The difference lies in the volume and density of the materials, not the weight.'
        #     },
        #     'parsing_error': None
        # }
        ```
        """  # noqa: E501
        _ = kwargs.pop("strict", None)
        if kwargs:
            msg = f"Received unsupported arguments {kwargs}"
            raise ValueError(msg)
        is_pydantic_schema = isinstance(schema, type) and is_basemodel_subclass(schema)
        if method == "function_calling":
            if schema is None:
                msg = (
                    "schema must be specified when method is 'function_calling'. "
                    "Received None."
                )
                raise ValueError(msg)
            # TODO: Update to pass in tool name as tool_choice if/when Mistral supports
            # specifying a tool.
            llm = self.bind_tools(
                [schema],
                tool_choice="any",
                ls_structured_output_format={
                    "kwargs": {"method": "function_calling"},
                    "schema": schema,
                },
            )
            if is_pydantic_schema:
                output_parser: OutputParserLike = PydanticToolsParser(
                    tools=[schema],  # type: ignore[list-item]
                    first_tool_only=True,  # type: ignore[list-item]
                )
            else:
                key_name = convert_to_openai_tool(schema)["function"]["name"]
                output_parser = JsonOutputKeyToolsParser(
                    key_name=key_name, first_tool_only=True
                )
        elif method == "json_mode":
            llm = self.bind(
                response_format={"type": "json_object"},
                ls_structured_output_format={
                    "kwargs": {
                        # this is correct - name difference with mistral api
                        "method": "json_mode"
                    },
                    "schema": schema,
                },
            )
            output_parser = (
                PydanticOutputParser(pydantic_object=schema)  # type: ignore[type-var, arg-type]
                if is_pydantic_schema
                else JsonOutputParser()
            )
        elif method == "json_schema":
            if schema is None:
                msg = (
                    "schema must be specified when method is 'json_schema'. "
                    "Received None."
                )
                raise ValueError(msg)
            response_format = _convert_to_openai_response_format(schema, strict=True)
            llm = self.bind(
                response_format=response_format,
                ls_structured_output_format={
                    "kwargs": {"method": "json_schema"},
                    "schema": schema,
                },
            )

            output_parser = (
                PydanticOutputParser(pydantic_object=schema)  # type: ignore[arg-type]
                if is_pydantic_schema
                else JsonOutputParser()
            )
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