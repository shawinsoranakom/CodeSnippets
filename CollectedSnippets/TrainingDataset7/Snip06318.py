async def ahas_perms(self, perm_list, obj=None):
        """See has_perms()"""
        if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")
        for perm in perm_list:
            if not await self.ahas_perm(perm, obj):
                return False
        return True