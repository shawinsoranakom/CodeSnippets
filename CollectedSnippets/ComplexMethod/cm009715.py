def test_chat_prompt_template_message_class_tuples_mixed_syntax() -> None:
    """Test mixing message class tuples with string tuples."""
    template = ChatPromptTemplate.from_messages(
        [
            (SystemMessage, "System prompt."),  # class tuple
            ("human", "{user_input}"),  # string tuple
            (AIMessage, "AI response."),  # class tuple
        ]
    )

    messages = template.format_messages(user_input="Hello!")

    assert len(messages) == 3
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert isinstance(messages[2], AIMessage)
    assert messages[0].content == "System prompt."
    assert messages[1].content == "Hello!"
    assert messages[2].content == "AI response."