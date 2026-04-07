def test_rename_backward_without_permissions(self):
        """
        Backward migration handles the case where permissions
        don't exist (e.g., they were manually deleted).
        """
        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0)
        # Apply the migration that renames OldModel to NewModel.
        call_command("migrate", "auth_tests", "0002", verbosity=0)

        Permission.objects.filter(content_type__app_label="auth_tests").delete()

        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="default",
            interactive=False,
            verbosity=0,
        )
        self.assertFalse(
            Permission.objects.filter(
                codename__in=["change_oldmodel", "change_newmodel"]
            ).exists()
        )

        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="default",
            interactive=False,
            verbosity=0,
        )