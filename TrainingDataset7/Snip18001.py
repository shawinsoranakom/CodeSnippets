def test_default_permissions(self):
        permission_content_type = ContentType.objects.get_by_natural_key(
            "auth", "permission"
        )
        Permission._meta.permissions = [
            ("my_custom_permission", "Some permission"),
        ]
        create_permissions(self.app_config, verbosity=0)

        # view/add/change/delete permission by default + custom permission
        self.assertEqual(
            Permission.objects.filter(
                content_type=permission_content_type,
            ).count(),
            5,
        )

        Permission.objects.filter(content_type=permission_content_type).delete()
        Permission._meta.default_permissions = []
        create_permissions(self.app_config, verbosity=0)

        # custom permission only since default permissions is empty
        self.assertEqual(
            Permission.objects.filter(
                content_type=permission_content_type,
            ).count(),
            1,
        )