async def test_close_async_uses_specialized_implementation(self):
        if (
            cache.close.__func__ is not BaseCache.close
            and cache.aclose.__func__ is BaseCache.aclose
        ):
            with mock.patch.object(cache, "close") as mocked:
                mocked.__func__ = lambda x: x
                await cache.aclose()
                mocked.assert_called_once()