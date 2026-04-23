async def aget_all_permissions(self, obj=None):
        return await _auser_get_permissions(self, obj, "all")