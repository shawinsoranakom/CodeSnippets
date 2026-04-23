async def test_cache_create_stream() -> None:
    _, prompts, system_prompt, _, cached_client = get_test_data()

    original_streamed_results: List[Union[str, CreateResult]] = []
    async for completion in cached_client.create_stream(
        [system_prompt, UserMessage(content=prompts[0], source="user")]
    ):
        original_streamed_results.append(copy.copy(completion))
    total_usage0 = copy.copy(cached_client.total_usage())

    cached_completion_results: List[Union[str, CreateResult]] = []
    async for completion in cached_client.create_stream(
        [system_prompt, UserMessage(content=prompts[0], source="user")]
    ):
        cached_completion_results.append(copy.copy(completion))
    total_usage1 = copy.copy(cached_client.total_usage())

    assert total_usage1.prompt_tokens == total_usage0.prompt_tokens
    assert total_usage1.completion_tokens == total_usage0.completion_tokens

    for original, cached in zip(original_streamed_results, cached_completion_results, strict=False):
        if isinstance(original, str):
            assert original == cached
        elif isinstance(original, CreateResult) and isinstance(cached, CreateResult):
            assert original.content == cached.content
            assert cached.cached
            assert not original.cached
        else:
            raise ValueError(f"Unexpected types : {type(original)} and {type(cached)}")