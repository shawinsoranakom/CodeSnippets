def test_shared_cache_ttl_refresh(self):
        """Test TTL refresh functionality with shared cache."""
        call_count = 0

        @cached(ttl_seconds=2, shared_cache=True, refresh_ttl_on_get=True)
        def ttl_refresh_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 10

        # Clear any existing cache
        ttl_refresh_function.cache_clear()

        # First call
        result1 = ttl_refresh_function(3)
        assert result1 == 30
        assert call_count == 1

        # Wait 1 second
        time.sleep(1)

        # Second call - should refresh TTL and use cache
        result2 = ttl_refresh_function(3)
        assert result2 == 30
        assert call_count == 1

        # Wait another 1.5 seconds (total 2.5s from first call, 1.5s from second)
        time.sleep(1.5)

        # Third call - TTL should have been refreshed, so still cached
        result3 = ttl_refresh_function(3)
        assert result3 == 30
        assert call_count == 1

        # Wait 2.1 seconds - now it should expire
        time.sleep(2.1)

        # Fourth call - should call function again
        result4 = ttl_refresh_function(3)
        assert result4 == 30
        assert call_count == 2

        # Cleanup
        ttl_refresh_function.cache_clear()