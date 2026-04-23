def test_simple_arguments(self):
        call_count = 0

        @thread_cached
        def simple_function(a: str, b: int, c: str = "default") -> str:
            nonlocal call_count
            call_count += 1
            return f"{a}-{b}-{c}"

        # First call with all positional args
        result1 = simple_function("test", 42, "custom")
        assert call_count == 1

        # Same args, all positional - should hit cache
        result2 = simple_function("test", 42, "custom")
        assert call_count == 1
        assert result1 == result2

        # Same values but last arg as keyword - creates different cache key
        result3 = simple_function("test", 42, c="custom")
        assert call_count == 2
        assert result1 == result3  # Same result, different cache entry

        # Different value - new cache entry
        result4 = simple_function("test", 43, "custom")
        assert call_count == 3
        assert result1 != result4