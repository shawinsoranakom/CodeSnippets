def setUp(self):
        self._original_permissions = Permission._meta.permissions[:]
        self._original_default_permissions = Permission._meta.default_permissions
        self.app_config = apps.get_app_config("auth")