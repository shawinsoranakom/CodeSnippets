async def aget(self, key, default=None, version=None):
        return await sync_to_async(self.get, thread_sensitive=True)(
            key, default, version
        )