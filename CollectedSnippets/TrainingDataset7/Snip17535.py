async def ahas_module_perms(self, user, app_label):
        return self.has_module_perms(user, app_label)