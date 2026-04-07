async def aget_user_permissions(self, obj=None):
        """See get_user_permissions()"""
        return await _auser_get_permissions(self, obj, "user")