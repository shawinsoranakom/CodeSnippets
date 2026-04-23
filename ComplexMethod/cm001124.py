async def test_async_cache_none_false_skips_storing_none(self):
        """``cache_none=False`` skips storing ``None`` so transient errors
        are retried on the next call instead of poisoning the cache."""
        call_count = 0
        results: list[int | None] = [None, None, 42]

        @cached(ttl_seconds=300, cache_none=False)
        async def maybe_none(x: int) -> int | None:
            nonlocal call_count
            result = results[call_count]
            call_count += 1
            return result

        # First call: returns None, NOT stored.
        assert await maybe_none(1) is None
        assert call_count == 1

        # Second call with same key: re-executes (None wasn't cached).
        assert await maybe_none(1) is None
        assert call_count == 2

        # Third call: returns 42, this time it IS stored.
        assert await maybe_none(1) == 42
        assert call_count == 3

        # Fourth call: cache hit on the stored 42.
        assert await maybe_none(1) == 42
        assert call_count == 3