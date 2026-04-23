async def aset_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        if self.set_many.__func__ is not BaseCache.set_many:
            return await sync_to_async(self.set_many, thread_sensitive=True)(
                data, timeout=timeout, version=version
            )
        for key, value in data.items():
            await self.aset(key, value, timeout=timeout, version=version)
        return []