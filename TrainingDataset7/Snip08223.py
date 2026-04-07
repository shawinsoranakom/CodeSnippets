async def aincr(self, key, delta=1, version=None):
        """See incr()."""
        if self.incr.__func__ is not BaseCache.incr:
            return await sync_to_async(self.incr, thread_sensitive=True)(
                key, delta=delta, version=version
            )
        value = await self.aget(key, self._missing_key, version=version)
        if value is self._missing_key:
            raise ValueError("Key '%s' not found" % key)
        new_value = value + delta
        await self.aset(key, new_value, version=version)
        return new_value