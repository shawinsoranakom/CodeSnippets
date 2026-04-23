async def afirst(self):
        return await sync_to_async(self.first)()