async def ahas_perm(self, user_obj, perm, obj=None):
        return user_obj.is_active and await super().ahas_perm(user_obj, perm, obj=obj)