async def test_chat_completion_n_parameter_non_streaming(
    client: openai.AsyncOpenAI, model_name: str
):
    """Test that n parameter returns multiple choices for non-streaming requests."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the opposite of big?"},
    ]

    # Test with n=3
    chat_completion = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=20,
        temperature=0.7,
        n=3,
        stream=False,
    )

    assert len(chat_completion.choices) == 3

    # Verify each choice has content and correct index
    for i, choice in enumerate(chat_completion.choices):
        assert choice.index == i
        assert choice.message.content is not None
        assert len(choice.message.content) > 0

    # Verify all responses are different (highly likely with temperature > 0)
    contents = [choice.message.content for choice in chat_completion.choices]
    assert len(set(contents)) > 1, "Expected different responses with n=3"