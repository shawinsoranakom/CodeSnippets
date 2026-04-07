async def adelete(self, key, version=None):
        return await sync_to_async(self.delete, thread_sensitive=True)(key, version)