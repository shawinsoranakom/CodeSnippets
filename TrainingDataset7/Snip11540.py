async def aupdate_or_create(self, **kwargs):
            return await sync_to_async(self.update_or_create)(**kwargs)