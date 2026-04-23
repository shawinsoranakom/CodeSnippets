def build_structured_output_base(self):
        schema_name = self.schema_name or "OutputModel"

        llm = get_llm(model=self.model, user_id=self.user_id, api_key=self.api_key)

        if not hasattr(llm, "with_structured_output"):
            msg = "Language model does not support structured output."
            raise TypeError(msg)
        if not self.output_schema:
            msg = "Output schema cannot be empty"
            raise ValueError(msg)

        output_model_ = build_model_from_schema(self.output_schema)
        output_model = create_model(
            schema_name,
            __doc__=f"A list of {schema_name}.",
            objects=(
                list[output_model_],
                Field(
                    description=f"A list of {schema_name}.",  # type: ignore[valid-type]
                    min_length=1,  # help ensure non-empty output
                ),
            ),
        )
        # Tracing config with token usage handler injected into the callbacks chain.
        # get_chat_result() reads "get_langchain_callbacks" as a callable, so we wrap
        # the list in a lambda to match its expected interface.
        token_handler = TokenUsageCallbackHandler()
        base_callbacks = self.get_langchain_callbacks()
        config_dict = {
            "display_name": self.display_name,
            "get_project_name": self.get_project_name,
            "get_langchain_callbacks": lambda: [*base_callbacks, token_handler],
        }
        # Generate structured output using Trustcall first, then fallback to Langchain if it fails
        result = self._extract_output_with_trustcall(llm, output_model, config_dict)
        if result is None:
            result = self._extract_output_with_langchain(llm, output_model, config_dict)
        self._token_usage = token_handler.get_usage()

        # OPTIMIZATION NOTE: Simplified processing based on trustcall response structure
        # Handle non-dict responses (shouldn't happen with trustcall, but defensive)
        if not isinstance(result, dict):
            return result

        # Extract first response and convert BaseModel to dict
        responses = result.get("responses", [])
        if not responses:
            return result

        # Convert BaseModel to dict (creates the "objects" key)
        first_response = responses[0]
        structured_data = first_response
        if isinstance(first_response, BaseModel):
            structured_data = first_response.model_dump()
        # Extract the objects array (guaranteed to exist due to our Pydantic model structure)
        return structured_data.get("objects", structured_data)