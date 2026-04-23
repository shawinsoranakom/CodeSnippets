def test_structured_output_verbosity(
    verbosity_format: str, streaming: bool, schema_format: str
) -> None:
    class MySchema(BaseModel):
        foo: str

    if verbosity_format == "model_kwargs":
        init_params: dict[str, Any] = {"model_kwargs": {"text": {"verbosity": "high"}}}
    else:
        init_params = {"verbosity": "high"}

    if streaming:
        init_params["streaming"] = True

    llm = ChatOpenAI(model="gpt-5", use_responses_api=True, **init_params)

    if schema_format == "pydantic":
        schema: Any = MySchema
    else:
        schema = MySchema.model_json_schema()

    structured_llm = llm.with_structured_output(schema)
    sequence = cast(RunnableSequence, structured_llm)
    binding = cast(RunnableBinding, sequence.first)
    bound_llm = cast(ChatOpenAI, binding.bound)
    bound_kwargs = binding.kwargs

    messages = [HumanMessage(content="Hello")]
    payload = bound_llm._get_request_payload(messages, **bound_kwargs)

    # Verify that verbosity is present in `text` param
    assert "text" in payload
    assert "verbosity" in payload["text"]
    assert payload["text"]["verbosity"] == "high"

    # Verify that schema is passed correctly
    if schema_format == "pydantic" and not streaming:
        assert payload["text_format"] == schema
    else:
        assert "format" in payload["text"]
        assert payload["text"]["format"]["type"] == "json_schema"