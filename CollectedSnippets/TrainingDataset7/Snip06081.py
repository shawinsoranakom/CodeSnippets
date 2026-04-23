async def aget_user_permissions(self, user_obj, obj=None):
        """See get_user_permissions()."""
        return await self._aget_permissions(user_obj, obj, "user")