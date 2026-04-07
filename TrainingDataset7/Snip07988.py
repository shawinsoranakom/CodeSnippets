async def aexists(self, session_key):
        return (
            session_key
            and (self.cache_key_prefix + session_key) in self._cache
            or await super().aexists(session_key)
        )