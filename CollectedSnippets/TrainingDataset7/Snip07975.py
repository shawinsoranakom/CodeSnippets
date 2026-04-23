async def asave(self, must_create=False):
        if self.session_key is None:
            return await self.acreate()
        if must_create:
            func = self._cache.aadd
        elif await self._cache.aget(await self.acache_key()) is not None:
            func = self._cache.aset
        else:
            raise UpdateError
        result = await func(
            await self.acache_key(),
            await self._aget_session(no_load=must_create),
            await self.aget_expiry_age(),
        )
        if must_create and not result:
            raise CreateError