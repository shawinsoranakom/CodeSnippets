async def __aiter__(self):
        if hasattr(self.object_list, "__aiter__"):
            async for obj in self.object_list:
                yield obj
        else:
            for obj in self.object_list:
                yield obj