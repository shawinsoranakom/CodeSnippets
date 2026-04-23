async def adelete_many(self, keys, version=None):
        if self.delete_many.__func__ is not BaseCache.delete_many:
            return await sync_to_async(self.delete_many, thread_sensitive=True)(
                keys, version=version
            )
        for key in keys:
            await self.adelete(key, version=version)