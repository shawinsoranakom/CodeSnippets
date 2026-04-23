def test_chat_input_schema(snapshot: SnapshotAssertion) -> None:
    prompt_all_required = ChatPromptTemplate(
        messages=[MessagesPlaceholder("history", optional=False), ("user", "${input}")]
    )
    assert set(prompt_all_required.input_variables) == {"input", "history"}
    assert prompt_all_required.optional_variables == []
    with pytest.raises(ValidationError):
        prompt_all_required.input_schema(input="")

    if version.parse("2.10") <= PYDANTIC_VERSION:
        assert _normalize_schema(
            prompt_all_required.get_input_jsonschema()
        ) == snapshot(name="required")
    prompt_optional = ChatPromptTemplate(
        messages=[MessagesPlaceholder("history", optional=True), ("user", "${input}")]
    )
    # input variables only lists required variables
    assert set(prompt_optional.input_variables) == {"input"}
    prompt_optional.input_schema(input="")  # won't raise error

    if version.parse("2.10") <= PYDANTIC_VERSION:
        assert _normalize_schema(prompt_optional.get_input_jsonschema()) == snapshot(
            name="partial"
        )