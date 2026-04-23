async def aflush(self):
        """See flush()."""
        self.clear()
        await self.adelete(self.session_key)
        self._session_key = None