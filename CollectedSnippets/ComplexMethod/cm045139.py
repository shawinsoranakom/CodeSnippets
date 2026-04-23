async def test_cache_token_usage() -> None:
    responses, prompts, system_prompt, replay_client, cached_client = get_test_data()

    response0 = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert isinstance(response0, CreateResult)
    assert not response0.cached
    assert response0.content == responses[0]
    actual_usage0 = copy.copy(cached_client.actual_usage())
    total_usage0 = copy.copy(cached_client.total_usage())

    response1 = await cached_client.create([system_prompt, UserMessage(content=prompts[1], source="user")])
    assert not response1.cached
    assert response1.content == responses[1]
    actual_usage1 = copy.copy(cached_client.actual_usage())
    total_usage1 = copy.copy(cached_client.total_usage())
    assert total_usage1.prompt_tokens > total_usage0.prompt_tokens
    assert total_usage1.completion_tokens > total_usage0.completion_tokens
    assert actual_usage1.prompt_tokens == actual_usage0.prompt_tokens
    assert actual_usage1.completion_tokens == actual_usage0.completion_tokens

    # Cached output.
    response0_cached = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert isinstance(response0, CreateResult)
    assert response0_cached.cached
    assert response0_cached.content == responses[0]
    total_usage2 = copy.copy(cached_client.total_usage())
    assert total_usage2.prompt_tokens == total_usage1.prompt_tokens
    assert total_usage2.completion_tokens == total_usage1.completion_tokens

    assert cached_client.actual_usage() == replay_client.actual_usage()
    assert cached_client.total_usage() == replay_client.total_usage()