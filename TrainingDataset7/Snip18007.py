def test_rename_skipped_if_router_disallows(self, _):
        # Create them manually, auto permissions won't create
        # since router disallows

        ct = ContentType.objects.create(app_label="auth_tests", model="oldmodel")
        Permission.objects.create(
            codename="change_oldmodel",
            name="Can change old model",
            content_type=ct,
        )

        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0)
        # Apply the migration that renames OldModel to NewModel.
        call_command("migrate", "auth_tests", "0002", verbosity=0)

        self.assertTrue(Permission.objects.filter(codename="change_oldmodel").exists())
        self.assertFalse(Permission.objects.filter(codename="change_newmodel").exists())

        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="default",
            interactive=False,
            verbosity=0,
        )