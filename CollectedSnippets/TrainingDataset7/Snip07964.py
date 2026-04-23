async def aload(self):
        return await sync_to_async(self.load)()