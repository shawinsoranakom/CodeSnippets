async def ahas_perm(self, user_obj, perm, obj=None):
        return perm in await self.aget_all_permissions(user_obj, obj)