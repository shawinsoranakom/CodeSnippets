async def ahas_perm(self, user, perm, obj=None):
        return self.has_perm(user, perm, obj)