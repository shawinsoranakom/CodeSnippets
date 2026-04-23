async def aadd(self, *objs, bulk=True):
            return await sync_to_async(self.add)(*objs, bulk=bulk)