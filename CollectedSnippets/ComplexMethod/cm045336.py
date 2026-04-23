async def test_token_limited_model_context_with_token_limit(
    model_client: ChatCompletionClient, token_limit: int
) -> None:
    model_context = TokenLimitedChatCompletionContext(model_client=model_client, token_limit=token_limit)
    messages: List[LLMMessage] = [
        UserMessage(content="Hello!", source="user"),
        AssistantMessage(content="What can I do for you?", source="assistant"),
        UserMessage(content="Tell what are some fun things to do in seattle.", source="user"),
    ]
    for msg in messages:
        await model_context.add_message(msg)

    retrieved = await model_context.get_messages()
    # Token limit set low, will remove some messages
    # OpenAI: keeps 2 messages (29 tokens with limit 30)
    # Ollama: keeps 1 message (20 tokens with limit 20)
    assert len(retrieved) < len(messages)  # Some messages removed due to token limit
    assert retrieved != messages  # Will not be equal to the original messages

    await model_context.clear()
    retrieved = await model_context.get_messages()
    assert len(retrieved) == 0

    # Test saving and loading state.
    for msg in messages:
        await model_context.add_message(msg)
    state = await model_context.save_state()
    await model_context.clear()
    await model_context.load_state(state)
    retrieved = await model_context.get_messages()
    assert len(retrieved) < len(messages)  # Some messages removed due to token limit
    assert retrieved != messages