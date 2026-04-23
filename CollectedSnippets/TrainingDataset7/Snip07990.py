async def asave(self, must_create=False):
        await super().asave(must_create)
        try:
            await self._cache.aset(
                await self.acache_key(),
                self._session,
                await self.aget_expiry_age(),
            )
        except Exception:
            logger.exception("Error saving to cache (%s)", self._cache)