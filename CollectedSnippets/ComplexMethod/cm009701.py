async def test_global_cache_abatch() -> None:
    global_cache = InMemoryCache()
    try:
        set_llm_cache(global_cache)
        chat_model = FakeListChatModel(
            cache=True, responses=["hello", "goodbye", "meow", "woof"]
        )
        results = await chat_model.abatch(["first prompt", "second prompt"])
        assert results[0].content == "hello"
        assert results[1].content == "goodbye"

        # Now try with the same prompt
        results = await chat_model.abatch(["first prompt", "first prompt"])
        assert results[0].content == "hello"
        assert results[1].content == "hello"

        global_cache = InMemoryCache()
        set_llm_cache(global_cache)
        assert global_cache._cache == {}
        results = await chat_model.abatch(["prompt", "prompt"])

        assert results[0].content == "meow"
        assert results[1].content == "meow"
    finally:
        set_llm_cache(None)