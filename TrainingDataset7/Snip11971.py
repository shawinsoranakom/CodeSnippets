async def alast(self):
        return await sync_to_async(self.last)()