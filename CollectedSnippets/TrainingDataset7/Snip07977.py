async def aexists(self, session_key):
        return bool(session_key) and await self._cache.ahas_key(
            self.cache_key_prefix + session_key
        )