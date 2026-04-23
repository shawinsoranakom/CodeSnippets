async def aclear_expired(cls):
        return await sync_to_async(cls.clear_expired)()