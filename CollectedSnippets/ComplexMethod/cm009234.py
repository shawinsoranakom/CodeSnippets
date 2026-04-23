def test_anthropic_generate() -> None:
    """Test generate method of anthropic."""
    chat = ChatAnthropic(model=MODEL_NAME)  # type: ignore[call-arg]
    chat_messages: list[list[BaseMessage]] = [
        [HumanMessage(content="How many toes do dogs have?")],
    ]
    messages_copy = [messages.copy() for messages in chat_messages]
    result: LLMResult = chat.generate(chat_messages)
    assert isinstance(result, LLMResult)
    for response in result.generations[0]:
        assert isinstance(response, ChatGeneration)
        assert isinstance(response.text, str)
        assert response.text == response.message.content
    assert chat_messages == messages_copy