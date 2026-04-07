def test_makemigrations_no_changes_no_apps(self):
        """
        makemigrations exits when there are no changes and no apps are
        specified.
        """
        out = io.StringIO()
        call_command("makemigrations", stdout=out)
        self.assertIn("No changes detected", out.getvalue())