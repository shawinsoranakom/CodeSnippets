async def ahas_key(self, key, version=None):
        if self.has_key.__func__ is not BaseCache.has_key:
            return await sync_to_async(self.has_key, thread_sensitive=True)(
                key, version=version
            )
        return (
            await self.aget(key, self._missing_key, version=version)
            is not self._missing_key
        )