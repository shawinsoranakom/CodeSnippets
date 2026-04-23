async def aincr_version(self, key, delta=1, version=None):
        """See incr_version()."""
        if self.incr_version.__func__ is not BaseCache.incr_version:
            return await sync_to_async(self.incr_version, thread_sensitive=True)(
                key, delta=delta, version=version
            )
        if version is None:
            version = self.version

        value = await self.aget(key, self._missing_key, version=version)
        if value is self._missing_key:
            raise ValueError("Key '%s' not found" % key)

        await self.aset(key, value, version=version + delta)
        await self.adelete(key, version=version)
        return version + delta