async def aget_all_permissions(self, user_obj, obj=None):
        return {
            *await self.aget_user_permissions(user_obj, obj=obj),
            *await self.aget_group_permissions(user_obj, obj=obj),
        }