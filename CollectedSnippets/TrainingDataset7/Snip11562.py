async def aclear(self):
            return await sync_to_async(self.clear)()