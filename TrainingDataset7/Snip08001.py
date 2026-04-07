async def aload(self):
        s = await self._aget_session_from_db()
        return self.decode(s.session_data) if s else {}