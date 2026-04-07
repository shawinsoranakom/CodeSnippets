async def aset(self, objs, *, bulk=True, clear=False):
            return await sync_to_async(self.set)(objs=objs, bulk=bulk, clear=clear)