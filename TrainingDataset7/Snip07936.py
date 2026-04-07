async def _aget_or_create_session_key(self):
        if self._session_key is None:
            self._session_key = await self._aget_new_session_key()
        return self._session_key