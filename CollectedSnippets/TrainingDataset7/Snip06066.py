async def aget_user_permissions(self, user_obj, obj=None):
        return await sync_to_async(self.get_user_permissions)(user_obj, obj)