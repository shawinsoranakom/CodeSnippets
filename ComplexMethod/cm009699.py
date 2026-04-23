def test_global_cache_sync() -> None:
    """Test that the global cache gets populated when cache = True."""
    global_cache = InMemoryCache()
    try:
        set_llm_cache(global_cache)
        chat_model = FakeListChatModel(
            cache=True, responses=["hello", "goodbye", "meow", "woof"]
        )
        assert (chat_model.invoke("How are you?")).content == "hello"
        # If the cache works we should get the same response since
        # the prompt is the same
        assert (chat_model.invoke("How are you?")).content == "hello"
        # The global cache should be populated
        assert len(global_cache._cache) == 1
        llm_result = list(global_cache._cache.values())
        chat_generation = llm_result[0][0]
        assert isinstance(chat_generation, ChatGeneration)
        assert chat_generation.message.content == "hello"
        # Verify that another prompt will trigger the call to the model
        assert chat_model.invoke("nice").content == "goodbye"
        # The local cache should be populated
        assert len(global_cache._cache) == 2
    finally:
        set_llm_cache(None)