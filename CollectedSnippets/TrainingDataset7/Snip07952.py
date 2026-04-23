async def aflush(self):
        self.clear()
        await self.adelete()
        self._session_key = None