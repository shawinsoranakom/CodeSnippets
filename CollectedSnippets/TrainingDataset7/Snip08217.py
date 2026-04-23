async def aget_many(self, keys, version=None):
        """See get_many()."""
        if self.get_many.__func__ is not BaseCache.get_many:
            return await sync_to_async(self.get_many, thread_sensitive=True)(
                keys, version=version
            )
        d = {}
        for k in keys:
            val = await self.aget(k, self._missing_key, version=version)
            if val is not self._missing_key:
                d[k] = val
        return d