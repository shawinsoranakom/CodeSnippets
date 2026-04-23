def test_help(self):
        """
        Test listing available commands output note when only core commands are
        available.
        """
        self.write_settings(
            "settings.py",
            extra="from django.core.exceptions import ImproperlyConfigured\n"
            "raise ImproperlyConfigured()",
        )
        args = ["help"]
        out, err = self.run_manage(args)
        self.assertOutput(out, "only Django core commands are listed")
        self.assertNoOutput(err)