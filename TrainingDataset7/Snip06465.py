async def aremove(self, *objs, bulk=True):
            return await sync_to_async(self.remove)(*objs, bulk=bulk)