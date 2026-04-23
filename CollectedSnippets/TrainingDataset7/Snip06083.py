async def aget_group_permissions(self, user_obj, obj=None):
        """See get_group_permissions()."""
        return await self._aget_permissions(user_obj, obj, "group")