def test_with_structured_output_json_schema_strict() -> None:
    class Response(BaseModel):
        """Response schema."""

        foo: str

    structured_model = ChatGroq(model="openai/gpt-oss-20b").with_structured_output(
        Response, method="json_schema", strict=True
    )

    assert isinstance(structured_model, RunnableSequence)
    first_step = structured_model.steps[0]
    assert isinstance(first_step, RunnableBinding)
    response_format = first_step.kwargs["response_format"]
    assert response_format["type"] == "json_schema"
    json_schema = response_format["json_schema"]
    assert json_schema["strict"] is True
    assert json_schema["name"] == "Response"
    assert json_schema["schema"]["properties"]["foo"]["type"] == "string"
    assert "foo" in json_schema["schema"]["required"]
    assert json_schema["schema"]["additionalProperties"] is False