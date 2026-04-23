async def test_async_function_returns_results_not_coroutines(self):
        """Test that cached async functions return actual results, not coroutines."""
        call_count = 0

        @cached(ttl_seconds=300)
        async def async_result_function(x: int) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return f"result_{x}"

        # First call
        result1 = await async_result_function(1)
        assert result1 == "result_1"
        assert isinstance(result1, str)  # Should be string, not coroutine
        assert call_count == 1

        # Second call - should return cached result (string), not coroutine
        result2 = await async_result_function(1)
        assert result2 == "result_1"
        assert isinstance(result2, str)  # Should be string, not coroutine
        assert call_count == 1  # Function should not be called again

        # Verify results are identical
        assert result1 is result2