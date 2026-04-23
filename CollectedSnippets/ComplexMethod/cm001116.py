async def test_async_function_caching(self):
        call_count = 0

        @thread_cached
        async def expensive_async_function(x: int, y: int = 0) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return x + y

        assert await expensive_async_function(1, 2) == 3
        assert call_count == 1

        assert await expensive_async_function(1, 2) == 3
        assert call_count == 1

        assert await expensive_async_function(1, y=2) == 3
        assert call_count == 2

        assert await expensive_async_function(2, 3) == 5
        assert call_count == 3