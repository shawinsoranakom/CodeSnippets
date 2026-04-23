async def aclear(self, *, bulk=True):
            return await sync_to_async(self.clear)(bulk=bulk)