def test_basic_allocate_and_reuse():
    cache = EncoderCacheManager(cache_size=10)
    req = MockRequest("r1", ["imgA"], [4])

    assert not cache.check_and_update_cache(req, 0)
    assert cache.can_allocate(req, 0, int(1e9), 0)

    cache.allocate(req, 0)

    assert cache.check_and_update_cache(req, 0)
    assert "r1" in cache.cached["imgA"]
    assert cache.num_free_slots == 6

    # Free twice to bring refcount to 0.
    cache.free_encoder_input(req, 0)
    cache.free_encoder_input(req, 0)

    assert not cache.cached["imgA"]
    assert "imgA" in cache.freeable
    assert cache.num_freeable_slots == 10
    assert cache.num_free_slots == 6