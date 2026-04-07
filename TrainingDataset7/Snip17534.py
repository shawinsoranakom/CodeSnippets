def has_module_perms(self, user, app_label):
        return (user.is_anonymous or user.is_active) and app_label == "app1"