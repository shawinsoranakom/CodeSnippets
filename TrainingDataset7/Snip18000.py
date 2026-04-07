def tearDown(self):
        Permission._meta.permissions = self._original_permissions
        Permission._meta.default_permissions = self._original_default_permissions
        ContentType.objects.clear_cache()