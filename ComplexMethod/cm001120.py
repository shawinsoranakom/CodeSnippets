async def test_async_cache_delete(self):
        """Test selective cache deletion functionality with async function."""
        call_count = 0

        @cached(ttl_seconds=300)
        async def async_deletable_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return x * 7

        # First call for x=1
        result1 = await async_deletable_function(1)
        assert result1 == 7
        assert call_count == 1

        # First call for x=2
        result2 = await async_deletable_function(2)
        assert result2 == 14
        assert call_count == 2

        # Second calls - should use cache
        assert await async_deletable_function(1) == 7
        assert await async_deletable_function(2) == 14
        assert call_count == 2

        # Delete specific entry for x=1
        was_deleted = async_deletable_function.cache_delete(1)
        assert was_deleted is True

        # Call with x=1 should execute function again
        result3 = await async_deletable_function(1)
        assert result3 == 7
        assert call_count == 3

        # Call with x=2 should still use cache
        assert await async_deletable_function(2) == 14
        assert call_count == 3

        # Try to delete non-existent entry
        was_deleted = async_deletable_function.cache_delete(99)
        assert was_deleted is False