async def acreate(self):
        while True:
            self._session_key = await self._aget_new_session_key()
            try:
                # Save immediately to ensure we have a unique entry in the
                # database.
                await self.asave(must_create=True)
            except CreateError:
                # Key wasn't unique. Try again.
                continue
            self.modified = True
            return