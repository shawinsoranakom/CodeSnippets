def test_mock_merge_system_messages_message_order() -> None:
    """Tests that message order is preserved after merging."""
    client = AnthropicChatCompletionClient(model="claude-3-haiku-20240307", api_key="fake-api-key")

    messages: List[LLMMessage] = [
        UserMessage(content="Question 1", source="user"),
        SystemMessage(content="Instruction 1"),
        SystemMessage(content="Instruction 2"),
        UserMessage(content="Question 2", source="user"),
        AssistantMessage(content="Answer", source="assistant"),
    ]

    merged_messages = client._merge_system_messages(messages)  # pyright: ignore[reportPrivateUsage]
    # The method is protected, but we need to test it
    assert len(merged_messages) == 4

    # 첫 번째 메시지는 UserMessage여야 함
    assert isinstance(merged_messages[0], UserMessage)
    assert merged_messages[0].content == "Question 1"

    # 두 번째 메시지는 병합된 SystemMessage여야 함
    assert isinstance(merged_messages[1], SystemMessage)
    assert merged_messages[1].content == "Instruction 1\nInstruction 2"

    # 나머지 메시지는 순서대로 유지되어야 함
    assert isinstance(merged_messages[2], UserMessage)
    assert merged_messages[2].content == "Question 2"
    assert isinstance(merged_messages[3], AssistantMessage)
    assert merged_messages[3].content == "Answer"