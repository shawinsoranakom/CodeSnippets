async def test_cache_basic_with_args() -> None:
    responses, prompts, system_prompt, _, cached_client = get_test_data()

    response0 = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert isinstance(response0, CreateResult)
    assert not response0.cached
    assert response0.content == responses[0]

    response1 = await cached_client.create([system_prompt, UserMessage(content=prompts[1], source="user")])
    assert not response1.cached
    assert response1.content == responses[1]

    # Cached output.
    response0_cached = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert isinstance(response0, CreateResult)
    assert response0_cached.cached
    assert response0_cached.content == responses[0]

    # Cache miss if args change.
    response2 = await cached_client.create(
        [system_prompt, UserMessage(content=prompts[0], source="user")], json_output=True
    )
    assert isinstance(response2, CreateResult)
    assert not response2.cached
    assert response2.content == responses[2]