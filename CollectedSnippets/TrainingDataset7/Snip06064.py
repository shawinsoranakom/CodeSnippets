async def aget_user(self, user_id):
        return await sync_to_async(self.get_user)(user_id)