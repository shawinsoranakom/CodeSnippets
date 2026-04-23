async def aget_user_permissions(self, obj=None):
        return await _auser_get_permissions(self, obj, "user")