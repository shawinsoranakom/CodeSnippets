def test_rename_permission_conflict(self):
        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0)

        ct = ContentType.objects.get(app_label="auth_tests", model="oldmodel")
        old_perm = Permission.objects.get(
            codename="change_oldmodel",
            name="Can change old model",
        )
        conflicting_perm = Permission.objects.create(
            codename="change_newmodel",
            name="Can change new model",
            content_type=ct,
        )

        with self.assertRaises(RuntimeError):
            # Apply the migration that renames OldModel to NewModel.
            call_command(
                "migrate",
                "auth_tests",
                "0002",
                database="default",
                interactive=False,
                stdout=self.stdout,
            )

        command_output = self.stdout.getvalue()

        self.assertIn(
            f"Failed to rename permission {old_perm.pk} "
            f"from '{old_perm.codename}' to '{conflicting_perm.codename}'. "
            f"Please resolve the conflict manually.",
            command_output,
        )

        self.assertTrue(Permission.objects.filter(codename="change_oldmodel").exists())

        with self.assertRaises(RuntimeError):
            call_command(
                "migrate",
                "auth_tests",
                "zero",
                database="default",
                interactive=False,
                verbosity=0,
            )