async def aload(self):
        try:
            data = await self._cache.aget(await self.acache_key())
        except Exception:
            # Some backends (e.g. memcache) raise an exception on invalid
            # cache keys. If this happens, reset the session. See #17810.
            data = None

        if data is None:
            s = await self._aget_session_from_db()
            if s:
                data = self.decode(s.session_data)
                await self._cache.aset(
                    await self.acache_key(),
                    data,
                    await self.aget_expiry_age(expiry=s.expire_date),
                )
            else:
                data = {}
        return data