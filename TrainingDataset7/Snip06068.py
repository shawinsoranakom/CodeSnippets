async def aget_group_permissions(self, user_obj, obj=None):
        return await sync_to_async(self.get_group_permissions)(user_obj, obj)