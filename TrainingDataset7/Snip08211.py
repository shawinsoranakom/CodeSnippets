async def aset(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        return await sync_to_async(self.set, thread_sensitive=True)(
            key, value, timeout, version
        )