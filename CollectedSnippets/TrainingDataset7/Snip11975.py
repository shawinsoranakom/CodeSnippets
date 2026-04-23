async def adelete(self):
        return await sync_to_async(self.delete)()