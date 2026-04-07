async def _aget_session(self, no_load=False):
        self.accessed = True
        try:
            return self._session_cache
        except AttributeError:
            if self.session_key is None or no_load:
                self._session_cache = {}
            else:
                self._session_cache = await self.aload()
        return self._session_cache