def test_verbosity_prints(self):
        # Create initial content type and permissions for OldModel.
        call_command("migrate", "auth_tests", "0001", verbosity=0)
        # Apply the migration that renames OldModel to NewModel.
        call_command("migrate", "auth_tests", "0002", verbosity=2, stdout=self.stdout)

        command_output = self.stdout.getvalue()
        self.assertIn(
            "Renamed permission(s): auth_tests.add_oldmodel → add_newmodel",
            command_output,
        )
        self.assertIn(
            "Renamed permission(s): auth_tests.change_oldmodel → change_newmodel",
            command_output,
        )
        self.assertIn(
            "Renamed permission(s): auth_tests.view_oldmodel → view_newmodel",
            command_output,
        )
        self.assertIn(
            "Renamed permission(s): auth_tests.delete_oldmodel → delete_newmodel",
            command_output,
        )

        call_command("migrate", "auth_tests", "0001", verbosity=2, stdout=self.stdout)

        command_output = self.stdout.getvalue()
        self.assertIn(
            "Renamed permission(s): auth_tests.add_newmodel → add_oldmodel",
            command_output,
        )
        self.assertIn(
            "Renamed permission(s): auth_tests.change_newmodel → change_oldmodel",
            command_output,
        )
        self.assertIn(
            "Renamed permission(s): auth_tests.view_newmodel → view_oldmodel",
            command_output,
        )
        self.assertIn(
            "Renamed permission(s): auth_tests.delete_newmodel → delete_oldmodel",
            command_output,
        )

        call_command(
            "migrate",
            "auth_tests",
            "zero",
            database="default",
            interactive=False,
            verbosity=0,
        )