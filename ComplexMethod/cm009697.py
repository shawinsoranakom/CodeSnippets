def test_local_cache_sync() -> None:
    """Test that the local cache is being populated but not the global one."""
    global_cache = InMemoryCache()
    local_cache = InMemoryCache()
    try:
        set_llm_cache(global_cache)
        chat_model = FakeListChatModel(
            cache=local_cache, responses=["hello", "goodbye"]
        )
        assert chat_model.invoke("How are you?").content == "hello"
        # If the cache works we should get the same response since
        # the prompt is the same
        assert chat_model.invoke("How are you?").content == "hello"
        # The global cache should be empty
        assert global_cache._cache == {}
        # The local cache should be populated
        assert len(local_cache._cache) == 1
        llm_result = list(local_cache._cache.values())
        chat_generation = llm_result[0][0]
        assert isinstance(chat_generation, ChatGeneration)
        assert chat_generation.message.content == "hello"
        # Verify that another prompt will trigger the call to the model
        assert chat_model.invoke("meow?").content == "goodbye"
        # The global cache should be empty
        assert global_cache._cache == {}
        # The local cache should be populated
        assert len(local_cache._cache) == 2
    finally:
        set_llm_cache(None)