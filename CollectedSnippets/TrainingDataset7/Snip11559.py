async def aremove(self, *objs):
            return await sync_to_async(self.remove)(*objs)