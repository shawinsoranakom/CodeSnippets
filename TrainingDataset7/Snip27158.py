def test_makemigrations_nonexistent_app_label(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            call_command("makemigrations", "nonexistent_app", stderr=err)
        self.assertIn(self.nonexistent_app_error, err.getvalue())