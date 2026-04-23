async def ahas_perm(self, perm, obj=None):
        return await _auser_has_perm(self, perm, obj=obj)