async def test_convert_message_functions(agent: OpenAIAgent) -> None:
    from autogen_ext.agents.openai._openai_agent import _convert_message_to_openai_message  # type: ignore

    user_msg = TextMessage(content="Hello", source="user")
    openai_user_msg = _convert_message_to_openai_message(user_msg)  # type: ignore
    assert openai_user_msg["role"] == "user"
    assert openai_user_msg["content"] == "Hello"

    sys_msg = TextMessage(content="System prompt", source="system")
    openai_sys_msg = _convert_message_to_openai_message(sys_msg)  # type: ignore
    assert openai_sys_msg["role"] == "system"
    assert openai_sys_msg["content"] == "System prompt"

    assistant_msg = TextMessage(content="Assistant reply", source="assistant")
    openai_assistant_msg = _convert_message_to_openai_message(assistant_msg)  # type: ignore
    assert openai_assistant_msg["role"] == "assistant"
    assert openai_assistant_msg["content"] == "Assistant reply"

    text_msg = TextMessage(content="Plain text", source="other")
    openai_text_msg = _convert_message_to_openai_message(text_msg)  # type: ignore
    assert openai_text_msg["role"] == "user"
    assert openai_text_msg["content"] == "Plain text"