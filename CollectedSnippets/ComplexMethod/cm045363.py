def test_structured_message() -> None:
    # Create a structured message with the test content
    message = StructuredMessage[TestContent](
        source="test_agent",
        content=TestContent(field1="test", field2=42),
    )

    # Check that the message type is correct
    assert message.type == "StructuredMessage[TestContent]"  # type: ignore[comparison-overlap]

    # Check that the content is of the correct type
    assert isinstance(message.content, TestContent)

    # Check that the content fields are set correctly
    assert message.content.field1 == "test"
    assert message.content.field2 == 42

    # Check that model_dump works correctly
    dumped_message = message.model_dump()
    assert dumped_message["source"] == "test_agent"
    assert dumped_message["content"]["field1"] == "test"
    assert dumped_message["content"]["field2"] == 42
    assert dumped_message["type"] == "StructuredMessage[TestContent]"