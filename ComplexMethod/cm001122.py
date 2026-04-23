def test_shared_vs_local_cache_isolation(self):
        """Test that shared and local caches are isolated."""
        shared_count = 0
        local_count = 0

        @cached(ttl_seconds=30, shared_cache=True)
        def shared_function(x: int) -> int:
            nonlocal shared_count
            shared_count += 1
            return x * 2

        @cached(ttl_seconds=30, shared_cache=False)
        def local_function(x: int) -> int:
            nonlocal local_count
            local_count += 1
            return x * 2

        # Clear caches
        shared_function.cache_clear()
        local_function.cache_clear()

        # Call both with same args
        shared_result = shared_function(5)
        local_result = local_function(5)

        assert shared_result == local_result == 10
        assert shared_count == 1
        assert local_count == 1

        # Call again - both should use their respective caches
        shared_function(5)
        local_function(5)
        assert shared_count == 1
        assert local_count == 1

        # Clear only shared cache
        shared_function.cache_clear()

        # Shared should recompute, local should still use cache
        shared_function(5)
        local_function(5)
        assert shared_count == 2
        assert local_count == 1

        # Cleanup
        shared_function.cache_clear()
        local_function.cache_clear()