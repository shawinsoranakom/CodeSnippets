def test_cache_delete(self):
        """Test selective cache deletion functionality."""
        call_count = 0

        @cached(ttl_seconds=300)
        def deletable_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 6

        # First call for x=1
        result1 = deletable_function(1)
        assert result1 == 6
        assert call_count == 1

        # First call for x=2
        result2 = deletable_function(2)
        assert result2 == 12
        assert call_count == 2

        # Second calls - should use cache
        assert deletable_function(1) == 6
        assert deletable_function(2) == 12
        assert call_count == 2

        # Delete specific entry for x=1
        was_deleted = deletable_function.cache_delete(1)
        assert was_deleted is True

        # Call with x=1 should execute function again
        result3 = deletable_function(1)
        assert result3 == 6
        assert call_count == 3

        # Call with x=2 should still use cache
        assert deletable_function(2) == 12
        assert call_count == 3

        # Try to delete non-existent entry
        was_deleted = deletable_function.cache_delete(99)
        assert was_deleted is False