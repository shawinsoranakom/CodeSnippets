def test_permission_rename_respects_other_db(self):
        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0)

        permission = Permission.objects.using("default").get(
            codename="add_oldmodel",
            name="Can add old model",
        )

        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0, database="other")
        # Apply the migration that renames OldModel to NewModel.
        call_command("migrate", "auth_tests", "0002", verbosity=0, database="other")

        permission.refresh_from_db()
        self.assertEqual(permission.codename, "add_oldmodel")
        self.assertFalse(
            Permission.objects.using("other").filter(codename="add_oldmodel").exists()
        )
        self.assertTrue(
            Permission.objects.using("other").filter(codename="add_newmodel").exists()
        )

        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="other",
            interactive=False,
            verbosity=0,
        )
        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="default",
            interactive=False,
            verbosity=0,
        )