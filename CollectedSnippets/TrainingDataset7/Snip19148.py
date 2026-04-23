async def test_incr_async_uses_specialized_implementation(self):
        await cache.aset("key", 1)
        if (
            cache.incr.__func__ is not BaseCache.incr
            and cache.aincr.__func__ is BaseCache.aincr
        ):
            with mock.patch.object(cache, "incr") as mocked:
                mocked.__func__ = lambda x: x
                await cache.aincr("key")
                mocked.assert_called_once()