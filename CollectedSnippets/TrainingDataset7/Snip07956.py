async def aexists(self, session_key):
        return await sync_to_async(self.exists)(session_key)