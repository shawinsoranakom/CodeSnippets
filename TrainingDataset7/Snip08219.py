async def aget_or_set(self, key, default, timeout=DEFAULT_TIMEOUT, version=None):
        """See get_or_set()."""
        if self.get_or_set.__func__ is not BaseCache.get_or_set:
            return await sync_to_async(self.get_or_set, thread_sensitive=True)(
                key, default, timeout=timeout, version=version
            )
        val = await self.aget(key, self._missing_key, version=version)
        if val is self._missing_key:
            if callable(default):
                default = default()
            await self.aadd(key, default, timeout=timeout, version=version)
            # Fetch the value again to avoid a race condition if another caller
            # added a value between the first aget() and the aadd() above.
            return await self.aget(key, default, version=version)
        return val