def test_reset_clears_all_state():
    """Test that reset() clears all cached entries and restores capacity."""
    manager = EncoderCacheManager(cache_size=20)

    req1 = MockRequest("req1", ["img1", "img2"], [5, 3])
    req2 = MockRequest("req2", ["img3"], [4])

    manager.allocate(req1, 0)
    manager.allocate(req1, 1)
    manager.allocate(req2, 0)
    manager.free_encoder_input(req1, 0)

    req3 = MockRequest("req3", ["img4"], [10])
    manager.free_encoder_input(req1, 1)
    manager.free_encoder_input(req2, 0)
    manager.can_allocate(req3, 0, int(1e9), 0)
    manager.allocate(req3, 0)

    assert len(manager.cached) > 0
    assert manager.num_free_slots < 20

    manager.reset()

    assert len(manager.cached) == 0
    assert len(manager.freeable) == 0
    assert len(manager.freed) == 0
    assert manager.num_free_slots == 20
    assert manager.num_freeable_slots == 20