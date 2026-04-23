async def acall(self, *args, **kwargs):
        if iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        return await sync_to_async(self.func)(*args, **kwargs)