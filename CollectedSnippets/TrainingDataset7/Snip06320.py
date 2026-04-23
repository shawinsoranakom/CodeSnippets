async def ahas_module_perms(self, app_label):
        """See has_module_perms()"""
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return await _auser_has_module_perms(self, app_label)