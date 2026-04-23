async def test_include_name_in_message() -> None:
    """Test that include_name_in_message parameter controls the name field."""

    # Test with UserMessage
    user_message = UserMessage(content="Hello, I am from Seattle.", source="Adam")

    # Test with include_name_in_message=True (default)
    result_with_name = to_oai_type(user_message, include_name_in_message=True)[0]
    assert "name" in result_with_name
    assert result_with_name["name"] == "Adam"  # type: ignore[typeddict-item]
    assert result_with_name["role"] == "user"
    assert result_with_name["content"] == "Hello, I am from Seattle."

    # Test with include_name_in_message=False
    result_without_name = to_oai_type(user_message, include_name_in_message=False)[0]
    assert "name" not in result_without_name
    assert result_without_name["role"] == "user"
    assert result_without_name["content"] == "Hello, I am from Seattle."

    # Test with AssistantMessage (should not have name field regardless)
    assistant_message = AssistantMessage(content="Hello, how can I help you?", source="Assistant")

    # Test with include_name_in_message=True
    result_assistant_with_name = to_oai_type(assistant_message, include_name_in_message=True)[0]
    assert "name" not in result_assistant_with_name
    assert result_assistant_with_name["role"] == "assistant"

    # Test with include_name_in_message=False
    result_assistant_without_name = to_oai_type(assistant_message, include_name_in_message=False)[0]
    assert "name" not in result_assistant_without_name
    assert result_assistant_without_name["role"] == "assistant"

    # Test with SystemMessage (should not have name field regardless)
    system_message = SystemMessage(content="You are a helpful assistant.")
    result_system_with_name = to_oai_type(system_message, include_name_in_message=True)[0]
    result_system_without_name = to_oai_type(system_message, include_name_in_message=False)[0]
    assert "name" not in result_system_with_name
    assert "name" not in result_system_without_name
    assert result_system_with_name["role"] == "system"
    assert result_system_without_name["role"] == "system"

    # Test default behavior (should include name when parameter not specified)
    result_default = to_oai_type(user_message)[0]  # include_name_in_message defaults to True
    assert "name" in result_default
    assert result_default["name"] == "Adam"