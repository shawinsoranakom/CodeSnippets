async def aget_or_create(self, *, through_defaults=None, **kwargs):
            return await sync_to_async(self.get_or_create)(
                through_defaults=through_defaults, **kwargs
            )