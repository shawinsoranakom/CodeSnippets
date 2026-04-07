def test_permission_rename(self):
        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0)
        # Apply the migration that renames OldModel to NewModel.
        call_command("migrate", "auth_tests", "0002", verbosity=0)

        actions = ContentType._meta.default_permissions

        for action in actions:
            self.assertFalse(
                Permission.objects.filter(codename=f"{action}_oldmodel").exists()
            )
            self.assertTrue(
                Permission.objects.filter(codename=f"{action}_newmodel").exists()
            )

        # Unapply that migration, renaming NewModel back to OldModel.
        call_command(
            "migrate",
            "auth_tests",
            "0001",
            database="default",
            interactive=False,
            verbosity=0,
        )

        for action in actions:
            self.assertTrue(
                Permission.objects.filter(codename=f"{action}_oldmodel").exists()
            )
            self.assertFalse(
                Permission.objects.filter(codename=f"{action}_newmodel").exists()
            )

        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="default",
            interactive=False,
            verbosity=0,
        )