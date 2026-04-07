async def ahas_module_perms(self, user_obj, app_label):
        """See has_module_perms()"""
        return user_obj.is_active and any(
            perm[: perm.index(".")] == app_label
            for perm in await self.aget_all_permissions(user_obj)
        )