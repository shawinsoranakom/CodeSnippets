async def aget_group_permissions(self, obj=None):
        """See get_group_permissions()"""
        return await _auser_get_permissions(self, obj, "group")