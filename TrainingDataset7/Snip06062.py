async def aauthenticate(self, request, **kwargs):
        return await sync_to_async(self.authenticate)(request, **kwargs)