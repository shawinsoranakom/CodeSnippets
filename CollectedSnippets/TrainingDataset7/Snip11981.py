async def aexists(self):
        return await sync_to_async(self.exists)()