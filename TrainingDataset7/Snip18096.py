def test_migrate_with_existing_target_permission(self):
        """
        Permissions may already exist:

        - Old workaround was to manually create permissions for proxy models.
        - Model may have been concrete and then converted to proxy.

        Output a reminder to audit relevant permissions.
        """
        proxy_model_content_type = ContentType.objects.get_for_model(
            Proxy, for_concrete_model=False
        )
        Permission.objects.create(
            content_type=proxy_model_content_type,
            codename="add_proxy",
            name="Can add proxy",
        )
        Permission.objects.create(
            content_type=proxy_model_content_type,
            codename="display_proxys",
            name="May display proxys information",
        )
        with captured_stdout() as stdout:
            with connection.schema_editor() as editor:
                update_proxy_permissions.update_proxy_model_permissions(apps, editor)
        self.assertIn(
            "A problem arose migrating proxy model permissions", stdout.getvalue()
        )