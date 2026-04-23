def test_structured_message_component() -> None:
    # Create a structured message with the test content
    format_string = "this is a string {field1} and this is an int {field2}"
    s_m = StructuredMessageFactory(input_model=TestContent, format_string=format_string)
    config = s_m.dump_component()
    s_m_dyn = StructuredMessageFactory.load_component(config)
    message = s_m_dyn.StructuredMessage(
        source="test_agent", content=s_m_dyn.ContentModel(field1="test", field2=42), format_string=s_m_dyn.format_string
    )

    assert isinstance(message.content, s_m_dyn.ContentModel)
    assert not isinstance(message.content, TestContent)
    assert message.content.field1 == "test"  # type: ignore[attr-defined]
    assert message.content.field2 == 42  # type: ignore[attr-defined]

    dumped_message = message.model_dump()
    assert dumped_message["source"] == "test_agent"
    assert dumped_message["content"]["field1"] == "test"
    assert dumped_message["content"]["field2"] == 42
    assert message.to_model_text() == format_string.format(field1="test", field2=42)