async def adelete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        try:
            obj = await self.model.objects.aget(session_key=session_key)
            await obj.adelete()
        except self.model.DoesNotExist:
            pass