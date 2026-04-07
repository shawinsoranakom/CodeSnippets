async def test_incr_version_async_uses_specialized_implementation(self):
        await cache.aset("key", "value", version=1)
        if (
            cache.incr_version.__func__ is not BaseCache.incr_version
            and cache.aincr_version.__func__ is BaseCache.aincr_version
        ):
            with mock.patch.object(cache, "incr_version") as mocked:
                mocked.__func__ = lambda x: x
                await cache.aincr_version("key")
                mocked.assert_called_once()