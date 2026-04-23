async def test_chat_prompt_template(chat_prompt_template: ChatPromptTemplate) -> None:
    """Test chat prompt template."""
    prompt = chat_prompt_template.format_prompt(foo="foo", bar="bar", context="context")
    assert isinstance(prompt, ChatPromptValue)
    messages = prompt.to_messages()
    assert len(messages) == 4
    assert messages[0].content == "Here's some context: context"
    assert messages[1].content == "Hello foo, I'm bar. Thanks for the context"
    assert messages[2].content == "I'm an AI. I'm foo. I'm bar."
    assert messages[3].content == "I'm a generic message. I'm foo. I'm bar."

    async_prompt = await chat_prompt_template.aformat_prompt(
        foo="foo", bar="bar", context="context"
    )

    assert async_prompt.to_messages() == messages

    string = prompt.to_string()
    expected = (
        "System: Here's some context: context\n"
        "Human: Hello foo, I'm bar. Thanks for the context\n"
        "AI: I'm an AI. I'm foo. I'm bar.\n"
        "test: I'm a generic message. I'm foo. I'm bar."
    )
    assert string == expected

    string = chat_prompt_template.format(foo="foo", bar="bar", context="context")
    assert string == expected

    string = await chat_prompt_template.aformat(foo="foo", bar="bar", context="context")
    assert string == expected