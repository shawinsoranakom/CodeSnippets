async def test_cache_structured_output_with_args() -> None:
    responses, prompts, system_prompt, _, cached_client = get_test_data(num_messages=4)

    class Answer(BaseModel):
        thought: str
        answer: str

    class Answer2(BaseModel):
        calculation: str
        answer: str

    response0 = await cached_client.create(
        [system_prompt, UserMessage(content=prompts[0], source="user")], json_output=Answer
    )
    assert isinstance(response0, CreateResult)
    assert not response0.cached
    assert response0.content == responses[0]

    response1 = await cached_client.create(
        [system_prompt, UserMessage(content=prompts[1], source="user")], json_output=Answer
    )
    assert not response1.cached
    assert response1.content == responses[1]

    # Cached output.
    response0_cached = await cached_client.create(
        [system_prompt, UserMessage(content=prompts[0], source="user")], json_output=Answer
    )
    assert isinstance(response0, CreateResult)
    assert response0_cached.cached
    assert response0_cached.content == responses[0]

    # Without the json_output argument, the cache should not be hit.
    response0 = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert isinstance(response0, CreateResult)
    assert not response0.cached
    assert response0.content == responses[2]

    # With a different output type, the cache should not be hit.
    response0 = await cached_client.create(
        [system_prompt, UserMessage(content=prompts[1], source="user")], json_output=Answer2
    )
    assert isinstance(response0, CreateResult)
    assert not response0.cached
    assert response0.content == responses[3]