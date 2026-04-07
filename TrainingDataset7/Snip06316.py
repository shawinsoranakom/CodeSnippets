async def ahas_perm(self, perm, obj=None):
        """See has_perm()"""
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return await _auser_has_perm(self, perm, obj)