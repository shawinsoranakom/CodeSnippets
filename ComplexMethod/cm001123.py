def test_tampered_cache_entry_rejected(self):
        """A tampered Redis entry is rejected and treated as a cache miss."""
        from backend.util.cache import _get_redis

        call_count = 0

        @cached(ttl_seconds=30, shared_cache=True)
        def tamper_test_fn(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        tamper_test_fn.cache_clear()

        # Populate the cache
        result = tamper_test_fn(7)
        assert result == 14
        assert call_count == 1

        # Find and tamper with the Redis key
        redis = _get_redis()
        keys = list(redis.scan_iter("cache:tamper_test_fn:*"))
        assert len(keys) >= 1, "Expected at least one cache key"

        for key in keys:
            raw: bytes | None = redis.get(key)  # type: ignore[assignment]
            assert raw is not None
            # Flip a byte in the signature portion to simulate tampering
            tampered = bytes([raw[0] ^ 0xFF]) + raw[1:]  # type: ignore[index]
            redis.set(key, tampered)

        # Next call should detect tampering and recompute
        result2 = tamper_test_fn(7)
        assert result2 == 14
        assert call_count == 2  # Had to recompute

        tamper_test_fn.cache_clear()