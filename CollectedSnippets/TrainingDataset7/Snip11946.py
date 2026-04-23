async def acount(self):
        return await sync_to_async(self.count)()