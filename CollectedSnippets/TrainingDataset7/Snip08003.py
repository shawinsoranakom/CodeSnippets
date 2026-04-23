async def aexists(self, session_key):
        return await self.model.objects.filter(session_key=session_key).aexists()