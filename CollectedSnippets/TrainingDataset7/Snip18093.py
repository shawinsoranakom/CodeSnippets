def test_user_still_has_proxy_model_permissions(self):
        user = User.objects.create()
        user.user_permissions.add(self.default_permission)
        user.user_permissions.add(self.custom_permission)
        for permission in [self.default_permission, self.custom_permission]:
            self.assertTrue(user.has_perm("auth_tests." + permission.codename))
        with connection.schema_editor() as editor:
            update_proxy_permissions.update_proxy_model_permissions(apps, editor)
        # Reload user to purge the _perm_cache.
        user = User._default_manager.get(pk=user.pk)
        for permission in [self.default_permission, self.custom_permission]:
            self.assertTrue(user.has_perm("auth_tests." + permission.codename))