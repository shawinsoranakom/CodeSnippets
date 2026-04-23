def test_warning_does_not_halt(self):
        """
        When there are only warnings or less serious messages, then Django
        should not prevent user from launching their project, so `check`
        command should not raise `CommandError` exception.

        In this test we also test output format.
        """

        self.write_settings(
            "settings.py",
            apps=[
                "admin_scripts.app_raising_warning",
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            sdict={"DEBUG": True},
        )
        args = ["check"]
        out, err = self.run_manage(args)
        expected_err = (
            "System check identified some issues:\n"  # No "CommandError: "
            "\n"
            "WARNINGS:\n"
            "?: A warning\n"
            "\n"
            "System check identified 1 issue (0 silenced).\n"
        )
        self.assertEqual(err, expected_err)
        self.assertNoOutput(out)