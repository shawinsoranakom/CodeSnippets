async def atouch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        return await sync_to_async(self.touch, thread_sensitive=True)(
            key, timeout, version
        )