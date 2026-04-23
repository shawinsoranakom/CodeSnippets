async def aclose(self, **kwargs):
        return await sync_to_async(self.close, thread_sensitive=True)(**kwargs)