def test_free_request_frees_all_inputs():
    manager = EncoderCacheManager(cache_size=10)
    req = MockRequest("req3", ["a", "b"], [2, 3])

    assert manager.can_allocate(req, 0, int(1e9), 0)
    manager.allocate(req, 0)

    assert manager.can_allocate(req, 1, int(1e9), 0)
    manager.allocate(req, 1)

    assert len(manager.cached["a"]) == 1
    assert len(manager.cached["b"]) == 1

    manager.free(req)

    assert not manager.cached["a"]
    assert not manager.cached["b"]
    assert "a" in manager.freeable
    assert "b" in manager.freeable
    assert manager.num_freeable_slots == 10