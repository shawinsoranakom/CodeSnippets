async def adelete(self, using=None, keep_parents=False):
        return await sync_to_async(self.delete)(
            using=using,
            keep_parents=keep_parents,
        )