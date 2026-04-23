async def aget_or_create(self, **kwargs):
            return await sync_to_async(self.get_or_create)(**kwargs)