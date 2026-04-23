async def adelete(self, session_key=None):
        return await sync_to_async(self.delete)(session_key)