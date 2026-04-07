def __bool__(self):
        return self.user.has_module_perms(self.app_label)