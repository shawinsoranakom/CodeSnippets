async def test_token_count_logics() -> None:
    phrases = [
        "This is a test message.",
        "This is another test message.",
        "This is yet another test message.",
        "Maybe even more messages?",
    ]
    reply_model_client = ReplayChatCompletionClient(phrases)

    messages = [UserMessage(content="How many tokens are in this message?", source="_")]

    token_count = reply_model_client.count_tokens(messages)
    assert token_count == 7

    _ = await reply_model_client.create(messages)
    remaining_tokens = reply_model_client.remaining_tokens(messages)
    assert remaining_tokens == 9988

    multiple_messages = [UserMessage(content="This is another test message.", source="_")]
    total_token_count = reply_model_client.count_tokens(messages + multiple_messages)
    assert total_token_count == 12

    before_cteate_usage = copy.deepcopy(reply_model_client.total_usage())
    completion: CreateResult = await reply_model_client.create(messages)

    assert completion.usage.prompt_tokens == 7
    assert completion.usage.completion_tokens == 5

    after_create_usage = reply_model_client.total_usage()
    assert after_create_usage.prompt_tokens > before_cteate_usage.prompt_tokens
    assert after_create_usage.completion_tokens > before_cteate_usage.completion_tokens

    before_cteate_stream_usage = copy.deepcopy(reply_model_client.total_usage())

    async for _ in reply_model_client.create_stream(messages):
        pass
    after_create_stream_usage = reply_model_client.total_usage()
    assert after_create_stream_usage.completion_tokens > before_cteate_stream_usage.completion_tokens
    assert after_create_stream_usage.prompt_tokens > before_cteate_stream_usage.prompt_tokens