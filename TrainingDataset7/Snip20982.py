async def __call__(self, *args, **kwargs):
                return await self.wrapped(*args, **kwargs)