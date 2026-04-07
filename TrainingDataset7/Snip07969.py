async def acache_key(self):
        return self.cache_key_prefix + await self._aget_or_create_session_key()