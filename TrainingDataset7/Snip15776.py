def test_output_format(self):
        """All errors/warnings should be sorted by level and by message."""

        self.write_settings(
            "settings.py",
            apps=[
                "admin_scripts.app_raising_messages",
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            sdict={"DEBUG": True},
        )
        args = ["check"]
        out, err = self.run_manage(args)
        expected_err = (
            "SystemCheckError: System check identified some issues:\n"
            "\n"
            "ERRORS:\n"
            "?: An error\n"
            "\tHINT: Error hint\n"
            "\n"
            "WARNINGS:\n"
            "a: Second warning\n"
            "obj: First warning\n"
            "\tHINT: Hint\n"
            "\n"
            "System check identified 3 issues (0 silenced).\n"
        )
        self.assertEqual(err, expected_err)
        self.assertNoOutput(out)